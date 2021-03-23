# golem-afl

*golem-afl* is an experimental test-fuzzing framework for https://www.golem.network/


## Running a Demo on yagna/goth Testnet

The minimal way to demonstrate the application is:

1. Launch your yagna/goth interactive [testing environment]:
   https://handbook.golem.network/requestor-tutorials/interactive-testing-environment
   .
2. In another terminal window, go to the project directory. 
3. Source your golem python environment.
4. Run the application as follows:  
```
$ YAGNA_APPKEY=ffe812d99751432b926318d9015e0716 \
  YAGNA_API_URL=http://172.19.0.6:6000 \
  GSB_URL=tcp://172.19.0.6:6010 \
  python golem-afl.py --nodes=2 --prj=default --run-time=1 --cycle=2 \
  --subnet=goth

```
   It will run two fuzzing cycles of demo application, one minute each on two nodes.
5. Examine the output in `_out_results`. Look at plots, crashes and fuzzing stats. 



## Principles of Operation

1. The fuzzed application must be instrumented with `alf-gcc` or `afl-llvm`.
2. A subdirectory for the tested project must be created in the `prj`
   directory. Put the application inside the new directory. The binary
   must be named eitrer `app` or `app-redirect` in case when the `@@`
   operator is used. The input cases belong to `inputs` subdirectry.   
3. Run the application `golem-afl.py`.
4. The application will create as many golem nodes as required by the parameter `--nodes`.
5. The project which is defined by the `--prj` option will be uploaded
   to the first node, unpacked and executed with `afl-fuzz`. After a
   delay given by the `--run-time` parameter (in minutes) the fuzzer
   gets killed and the output directory `out` is downloaded. The first
   node runs as the master, the other nodes as slaves.
6. The process is repeated until the required number of cycles
   (`--cycles`) is reached. Each time the queue of all nodes gets
   copied to all the other nodes so that they can share interresting
   paths.
7. The fuzzing starts with the master node only. In the fuzzer has
   finished the determinisitic phase (ie. all paths have been
   discovered), the slave nodes also start to fuzz. 
8. The results go to the `__out_results` directory organised by cycle
   number and fuzzer number (node number). After each cycle a plot
   utility is executed to visualize the results of the cycle. 


The project has started as a part of [Grants Round 9 Hackathon
Golem Mainnet Hackathon @ GR9 - Open Track]: https://gitcoin.co/issue/golemfactory/hackathons/11/100025157]

Video:

Presentation: 

