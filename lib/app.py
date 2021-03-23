import subprocess
import re
import os


"""cargo_test_app application."""
class App:

    def __init__(self, args):
        self.args = args
        self.prj_dir = f"prj/{self.args.prj}"
        self.first_cycle_done = False
        
    def prepare_empty_directories(self):
        os.system("rm -rf _work _out_log _out_step _out_out  _out_results")
        os.system("mkdir _out_log _out_step _out_out _out_results")

    def extract_all_outputs(self, collection, tar_prefix, nodes):
        os.system(f"rm -rf {collection}")
        os.system(f"mkdir {collection}")
        for i in range(nodes):
            os.system(f"(cd {collection};  tar xzf {tar_prefix}{i}.tgz out/fuzzer{i})")
        
    def make_plots(self, collection, nodes):
        for i in range(nodes):
            os.system(f"mkdir {collection}/plots{i}")
            os.system(f"afl-plot {collection}/out/fuzzer{i} {collection}/plots{i}")

    def make_task_tar(self, continuation, collection):
        os.system("rm -rf _work")
        os.system("mkdir _work")
        os.system(f"cp -r {self.prj_dir}/* _work")
        if continuation:
            print(f"cp -r {collection}/out _work")
            os.system(f"cp -r {collection}/out _work")
            
        os.system("(cd _work; tar czf ../_out_step/task.tgz *)")
        os.system("rm -rf  _out_out")
        os.system("mkdir  _out_out")
        
    def make_step_sh(self, node, first_run, with_redirect, dummy):        
        master_slave =  "S" if node > 0 else "M"
        input_file = "-i inputs" if first_run else "-i-"
        app = "app_redirect" if with_redirect else "app"
        redirect = "@@" if with_redirect else "" 
        f = open(f"_out_step/step{node}.sh", "w")
#        f.write("trap \"echo trap >> /golem/work/output.txt\" EXIT\n")
        f.write("cd /golem/work\n")
        f.write("mkdir -p out\n")
        f.write(f"echo start >> /golem/work/output.txt\n")
        if not dummy:
            f.write("tar xzf task.tgz\n")
            f.write(f"chmod +x /afl-fuzz {app}\n")
            f.write("export AFL_SKIP_CPUFREQ=1\n")
            #        f.write(f"./{app} inputs/musil.txt &>> /golem/work/output.txt\n")
            f.write(f"(timeout {(self.args.run_time*60)}s /afl-fuzz {input_file} -o out -{master_slave} fuzzer{node} ./{app} {redirect}) &>> /golem/work/output.txt || true \n")
        f.write(f"echo stop >> /golem/work/output.txt\n")        
        f.write("sleep 1\n")
        f.write("tar czf /golem/work/output.tgz out || true\n")
        f.close()

    def parse_cycles_done(self, collection_dir):
        file = open(f"{collection_dir}/out/fuzzer0/fuzzer_stats", "r")
        for aline in file:
            match = re.search(r"cycles_done\s+[:]\s*(\d+)", aline)
            if match:
                return int(match.group(1))
        file.close()
        return 0
        
