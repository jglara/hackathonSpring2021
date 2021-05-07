from subprocess import Popen
import socket
from typing import Dict, List
import time
import os

def generate_mahimahi_command(mahimahi_settings: Dict, online, cca_name, ep_id, data_dir) -> str:
    loss_directive = ""
    if mahimahi_settings.get('downlink-loss'):
        loss_directive += "mm-loss downlink %f" % mahimahi_settings.get('downlink-loss')
    
    if mahimahi_settings.get('uplink-loss'):
        loss_directive += "mm-loss uplink %f" % mahimahi_settings.get('uplink-loss')

    if mahimahi_settings.get('downlink_queue_options'):
        downlink_queue_options = "--downlink-queue={} --downlink-queue-args=".format(mahimahi_settings.get('downlink-queue-type')) + ",".join(
            ["%s=%s" % (key, value)
            for key, value in mahimahi_settings.get('downlink_queue_options').items()]
        )
    else:
        downlink_queue_options = ""

    if mahimahi_settings.get('uplink_queue_options'):
        uplink_queue_options = "--uplink-queue={} --uplink-queue-args=".format(mahimahi_settings.get('uplink-queue-type')) + ",".join(
            ["%s=%s" % (key, value)
             for key, value in mahimahi_settings.get('uplink_queue_options').items()]
        )
    else:
        uplink_queue_options = ""

    if online:
        online_option="--meter-uplink --meter-uplink-delay"
    else:
        online_option = ""

    return "mm-delay {delay} {loss_directive} mm-link traces/{trace_file} traces/{trace_file} {downlink_queue_options} {uplink_queue_options} --downlink-log={data_dir}/{cca}_acklink_run{ep_id}.log --uplink-log={data_dir}/{cca}_datalink_run{ep_id}.log {online_option}".format(
        delay=mahimahi_settings['delay'],
        downlink_queue_options=downlink_queue_options,
        uplink_queue_options=uplink_queue_options,
        loss_directive=loss_directive,
        trace_file=mahimahi_settings['trace_file'],
        data_dir=data_dir,
        ep_id=ep_id,
        cca=cca_name,
        online_option=online_option
    )


def get_open_tcp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_episode(
        ep_id: int,
        data_dir: str,
        mahimahi_settings: Dict,
        online,
        port: int,
        seconds_to_run: int,
        cca: str,
        cca_name: str):

    mahimahi_cmd = generate_mahimahi_command(mahimahi_settings, online, cca_name, ep_id, data_dir)
    cmd = "{} -- sh -c 'iperf -c $MAHIMAHI_BASE -p {} -Z {} -t {}'".format(mahimahi_cmd, port, cca, seconds_to_run)
    print("launching {}".format(cmd))
    iperf_client = Popen(cmd, shell=True)
    iperf_client.wait(timeout=seconds_to_run * 2)


def run_experiment(num_episodes: int, seconds_to_run: int, cca: str, cca_name: str, data_dir: str, mahimahi_settings: Dict, online):

    # launch iperf server
    port = get_open_tcp_port()
    cmd = "iperf -s -p {}".format(port)
    print("launching {}".format(cmd))
    iperf_server = Popen(cmd, shell=True)
    
    for i in range(1, num_episodes+1):
        run_episode(i, data_dir, mahimahi_settings, online,
                    port,
                    seconds_to_run,
                    cca, cca_name)

    iperf_server.terminate()
    
        
import argparse
if __name__ == "__main__":
    mahimahi_settings = {
        "nepal_to_aws_india" : {
            'delay': 88,
            'uplink-loss': 0.0477,
            'uplink-queue-type': 'droptail',
            'trace_file': '0.57mbps-poisson.trace',
            'uplink-queue-type': 'droptail',
            'uplink_queue_options': {
                'packets': 14
            }
        },
        "mexico_cellular_to_aws_california" : {
            'delay': 28,
            'uplink-loss': 0.0477,
            'uplink-queue-type': 'droptail',
            'trace_file': '0.57mbps-poisson.trace',
            'uplink-queue-type': 'droptail',
            'uplink_queue_options': {
                'packets': 14
            }

        },
        "aws_brazil_to_colombia_cellular" : {
            'delay': 130,
            'uplink-queue-type': 'droptail',
            'trace_file': '3.04mbps-poisson.trace',
            'uplink_queue_options': {            
            'packets': 426
            }
        },
        "india_to_aws_india" : {
            'delay': 27,
            'uplink-queue-type': 'droptail',
            'trace_file': '100.42mbps.trace',
            'uplink_queue_options': {            
                'packets': 173
            }
        },
        "aws_korea_to_china" : {
            'delay': 51,
            'uplink-loss' : 0.0006,
            'uplink-queue-type': 'droptail',
            'trace_file': '77.72mbps.trace',
            'uplink_queue_options': {            
                'packets': 94
            }
        },
        "evo_test_1" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace_evo_draining.out',
            'uplink_queue_options': {            
                'bytes': 2500000
            }
        },
        "evo_test_2" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace_50_100_150.out',
            'uplink_queue_options': {            
                'bytes': 2500000
            }
        },

        "TMobile_LTE_driving" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'TMobile-LTE-driving.up',
            'uplink_queue_options': {            
                'bytes': 2500000
            }
        },

        "Verizon_LTE_driving" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'Verizon-LTE-driving.up',
            'uplink_queue_options': {            
                'bytes': 1500000
            }
        },
        
        "home" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace-1552925703-home1-static',
            'uplink_queue_options': {            
                'bytes': 1500000
            }
        },

        "taxi" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace-1552767958-taxi1',
            'uplink_queue_options': {            
                'bytes': 1500000
            }
        },

        "bus" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace-1553114405-bus',
            'uplink_queue_options': {            
                'bytes': 1500000
            }
        },

        "walking" : {
            'delay': 10,
            'uplink-queue-type': 'droptail',
            'trace_file': 'trace-1553189663-ts-walking',
            'uplink_queue_options': {            
                'bytes': 1500000
            }
        },

        
    }
    

    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', '-e', type=int, default=3)
    parser.add_argument('--cca', '-c', type=str, required=True)
    parser.add_argument('--cca-name', '-n', type=str)
    parser.add_argument('--running_time', '-r', type=int, default=10)
    parser.add_argument('--data-dir', '-d', type=str, default="results")
    parser.add_argument('--mahimahi-settings', '-m', type=str, default="evo_test_1")
    parser.add_argument('--online', default=False, action='store_true')
    args = parser.parse_args()

    if not args.mahimahi_settings in mahimahi_settings:
        print("Invalid settings. Valid ones are: {}".format(list(mahimahi_settings.keys())))
    else:
        data_dir = "{}/{}".format(args.data_dir, args.mahimahi_settings)

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        for cca in args.cca.split():
            if None == args.cca_name:
                cca_name = cca
            else:
                cca_name = args.cca_name            

            run_experiment(args.episodes, args.running_time, cca, cca_name, data_dir, mahimahi_settings[args.mahimahi_settings], args.online)

    
