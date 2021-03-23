#!/usr/bin/env python3
import asyncio
from datetime import (datetime, timedelta)
import pathlib
import sys
import os

from yapapi import (
    Executor,
    NoPaymentAccountError,
    Task,
    WorkContext,
    windows_event_loop_fix,
)
from yapapi.log import enable_default_logger, log_summary, log_event_repr  # noqa
from yapapi.package import vm
from yapapi.rest.activity import BatchTimeoutError

script_dir = pathlib.Path(__file__).resolve().parent
lib_dir = script_dir / "lib"
sys.path.append(str(lib_dir))

import text_colors
import argument_parser
from app import App


async def main(app: App):
    package = await vm.repo(
        # using existing image for 'blender' example
        image_hash="3fc93eca1f720bb7a2d6fa6394a03b883b28ff3fbe3d768f6f858924",
        #        "9a3b5d67b0b27746283cb5f287c13eab1beaa12d92a9f536b747c7ae",
        min_mem_gib=1.0,
        min_storage_gib=2.0,
    )

    async def worker(ctx: WorkContext, tasks):
        cwd = pathlib.Path.cwd()
        remote_tar = "/golem/work/task.tgz"
        remote_sh = "/golem/entrypoint/step.sh"
        remote_out = "/golem/work/output.txt"
        remote_pack = "/golem/work/output.tgz"
        local_tar = "_out_step/task.tgz"
        
        async for task in tasks:
            print(task)
            local_out = f"_out_log/output{task.id}.txt"
            local_pack = f"_out_out/output{task.data}.tgz"
            local_sh = f"_out_step/step{task.data}.sh"
            ctx.send_file(local_sh, remote_sh)
            ctx.send_file(local_tar, remote_tar)            
            ctx.run("/bin/bash", remote_sh)
            ctx.download_file(remote_out, local_out)
            ctx.download_file(remote_pack, local_pack)
            try:
                yield ctx.commit(timeout=timedelta(seconds=1800))
                task.accept_result(result=local_out)
            except BatchTimeoutError:
                print(
                    f"{text_colors.RED}"
                    f"Task {task} timed out on {ctx.provider_name}, time: {task.running_time}"
                    f"{text_colors.DEFAULT}"
                )
                raise

    tmo = app.args.run_time + 1
    if tmo < 6: tmo = 6
    if tmo > 30: tmo = 30
    print(f"tmo {tmo}")
    timeout = timedelta(minutes=(tmo))

    # By passing `event_consumer=log_summary()` we enable summary logging.
    # See the documentation of the `yapapi.log` module on how to set
    # the level of detail and format of the logged information.
    async with Executor(
            package=package,
            max_workers=app.args.nodes,
            budget=10.0,
            timeout=timeout,
            subnet_tag=app.args.subnet_tag,
            driver=app.args.driver,
            network=app.args.network,
            event_consumer=log_summary(log_event_repr),
    ) as executor:
        start_time = datetime.now()
        async for task in executor.submit(worker, [Task(data=node) for node in range(app.args.nodes)]):
            print(
                f"{text_colors.CYAN}"
                f"total time: {datetime.now() - start_time}"
                f"{text_colors.DEFAULT}"
            )

def run_one_batch(app, cycle):
    with_redirect = os.path.exists(f"{app.prj_dir}/app_redirect")
    node_cnt = 1
    if app.first_cycle_done:
        node_cnt = app.args.nodes
    
    for node in range(app.args.nodes):
        app.make_step_sh(node, cycle == 0, with_redirect, node >= node_cnt)

    previous_collection_dir = f"_out_results/cycle{cycle-1}"
    app.make_task_tar(cycle > 0, previous_collection_dir)
    task = loop.create_task(main(app=app))
    try:
        loop.run_until_complete(task)
    except NoPaymentAccountError as e:
        print(
            f"{text_colors.RED}"
            f"No payment account initialized for driver `{e.required_driver}` "
            f"and network `{e.required_network}`.\n\n"
            f"{text_colors.DEFAULT}"
        )
    except KeyboardInterrupt:
        print(
            f"{text_colors.YELLOW}"
            "Shutting down gracefully, please wait a short while "
            "or press Ctrl+C to exit immediately..."
            f"{text_colors.DEFAULT}"
        )
        task.cancel()
        try:
            loop.run_until_complete(task)
            print(
                f"{text_colors.YELLOW}"
                "Shutdown completed, thank you for waiting!"
                f"{text_colors.DEFAULT}"
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    collection_dir = f"_out_results/cycle{cycle}"
    app.extract_all_outputs(collection_dir, "../../_out_out/output", node_cnt)
    if not app.first_cycle_done:
        app.first_cycle_done = app.parse_cycles_done(collection_dir) > 0
    app.make_plots(collection_dir, node_cnt)
        
if __name__ == "__main__":
    parser = argument_parser.build_parser("Run a fuzz test")
    parser.set_defaults(log_file="golem-afl.log")
    app = App(parser.parse_args())

    print(
        f"{text_colors.CYAN}"
        f"cycle: {app.args.cycle} nodes: {app.args.nodes} "
        f"{text_colors.DEFAULT}"
    )

    windows_event_loop_fix()
    enable_default_logger(
        log_file=app.args.log_file,
        debug_activity_api=True,
        debug_market_api=True,
        debug_payment_api=True,
    )

    app.prepare_empty_directories()
    
    loop = asyncio.get_event_loop()

    for batch in range(app.args.cycle):
        run_one_batch(app, batch)
