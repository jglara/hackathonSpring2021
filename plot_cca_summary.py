#!/usr/bin/env python

from os import path
import sys
import math
import itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse
import yaml
import tunnel_graph
import pdb


def parse_config(schemes_config):
    with open(schemes_config) as config:
        return yaml.load(config)


def verify_schemes(schemes_config, schemes):
    schemes = schemes.split()
    all_schemes = parse_config(schemes_config)['schemes'].keys()

    for cc in schemes:
        if cc not in all_schemes:
            sys.exit('%s is not a scheme included in ./config.yml' % cc)


def parse_plot():
    parser = argparse.ArgumentParser(
        description='plot throughput and delay graphs for schemes in tests')

    parser.add_argument(
        '--schemes', metavar='"SCHEME1 SCHEME2..."',
        help='analyze a space-separated list of schemes ')
    
    parser.add_argument(
        '--data-dir', metavar='DIR',
        default='results',
        help='directory that contains logs')

    parser.add_argument(
        '--schemes-config',
        default='./config.yaml',
        help='Configuration of schemes')

    parser.add_argument('--episodes', '-e', type=int, default=3)


    args = parser.parse_args()
    if args.schemes is not None:
        verify_schemes(args.schemes_config, args.schemes)

    return args


class Plot(object):
    def __init__(self, args):
        self.data_dir = path.abspath(args.data_dir)
        self.cc_schemes = args.schemes.split()
        self.expt_title = self.data_dir
        self.episodes = args.episodes
        self.include_acklink= False
        self.schemes_config = args.schemes_config
        self.flows = 0

    def parse_tunnel_log(self, cc, run_id):
        log_prefix = cc

        error = False
        ret = None

        link_directions = ['datalink']
        if self.include_acklink:
            link_directions.append('acklink')

        for link_t in link_directions:
            log_name = log_prefix + '_%s_run%s.log' % (link_t, run_id)
            log_path = path.join(self.data_dir, log_name)

            if not path.isfile(log_path):
                sys.stderr.write('Warning: %s does not exist\n' % log_path)
                error = True
                continue

            tput_graph = cc + '_%s_throughput_run%s.png' % (link_t, run_id)
            tput_graph_path = path.join(self.data_dir, tput_graph)

            delay_graph = cc + '_%s_delay_run%s.png' % (link_t, run_id)
            delay_graph_path = path.join(self.data_dir, delay_graph)

            sys.stderr.write('$ tunnel_graph %s\n' % log_path)
            try:
                tunnel_results = tunnel_graph.TunnelGraph(
                    tunnel_log=log_path,
                    throughput_graph=tput_graph_path,
                    delay_graph=delay_graph_path).run()
            except Exception as exception:
                sys.stderr.write('Error: %s\n' % exception)
                sys.stderr.write('Warning: "tunnel_graph %s" failed but '
                                 'continued to run.\n' % log_path)
                error = True

            if error:
                continue

            if link_t == 'datalink':
                ret = tunnel_results
                duration = tunnel_results['duration'] / 1000.0

        if error:
            return None

        return ret


    def eval_performance(self):
        perf_data = {}

        for cc in self.cc_schemes:
            perf_data[cc] = {}

        cc_id = 0
        run_id = 1

        while cc_id < len(self.cc_schemes):
            cc = self.cc_schemes[cc_id]
            perf_data[cc][run_id] = self.parse_tunnel_log(cc, run_id)
            
            run_id += 1
            if run_id > self.episodes:
                run_id = 1
                cc_id += 1

#        for cc in self.cc_schemes:
#            for run_id in list(range(1, 1 + self.episodes)):
#                perf_data[cc][run_id] = perf_data[cc][run_id].get()
#
#                if perf_data[cc][run_id] is None:
#                    continue
#
        return perf_data


    def xaxis_log_scale(self, ax, min_delay, max_delay):
        if min_delay < -2:
            x_min = int(-math.pow(2, math.ceil(math.log(-min_delay, 2))))
        elif min_delay < 0:
            x_min = -2
        elif min_delay < 2:
            x_min = 0
        else:
            x_min = int(math.pow(2, math.floor(math.log(min_delay, 2))))

        if max_delay < -2:
            x_max = int(-math.pow(2, math.floor(math.log(-max_delay, 2))))
        elif max_delay < 0:
            x_max = 0
        elif max_delay < 2:
            x_max = 2
        else:
            x_max = int(math.pow(2, math.ceil(math.log(max_delay, 2))))

        symlog = False
        if x_min <= -2:
            if x_max >= 2:
                symlog = True
        elif x_min == 0:
            if x_max >= 8:
                symlog = True
        elif x_min >= 2:
            if x_max > 4 * x_min:
                symlog = True

        if symlog:
            ax.set_xscale('symlog', basex=2, linthreshx=2, linscalex=0.5)
            ax.set_xlim(x_min, x_max)
            ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))



    def plot_throughput_delay(self, data):
        min_raw_delay = float("inf")
        min_mean_delay = float("inf")
        max_raw_delay = float("-inf")
        max_mean_delay = float("-inf")

        fig_raw, ax_raw = plt.subplots()
        fig_mean, ax_mean = plt.subplots()

        schemes_config = parse_config(self.schemes_config)['schemes']
        for cc in data:
            if not data[cc]:
                sys.stderr.write('No performance data for scheme %s\n' % cc)
                continue

            value = data[cc]
            cc_name = schemes_config[cc]['name']
            color = schemes_config[cc]['color']
            marker = schemes_config[cc]['marker']
            y_data, x_data = zip(*value)

            # update min and max raw delay
            min_raw_delay = min(min(x_data), min_raw_delay)
            max_raw_delay = max(max(x_data), max_raw_delay)

            # plot raw values
            ax_raw.scatter(x_data, y_data, color=color, marker=marker,
                           label=cc_name, clip_on=False)

            # plot the average of raw values
            x_mean = np.mean(x_data)
            y_mean = np.mean(y_data)

            # update min and max mean delay
            min_mean_delay = min(x_mean, min_mean_delay)
            max_mean_delay = max(x_mean, max_mean_delay)

            ax_mean.scatter(x_mean, y_mean, color=color, marker=marker,
                            clip_on=False)
            ax_mean.annotate(cc_name, (x_mean, y_mean))

        for fig_type, fig, ax in [('raw', fig_raw, ax_raw),
                                  ('mean', fig_mean, ax_mean)]:
            if fig_type == 'raw':
                self.xaxis_log_scale(ax, min_raw_delay, max_raw_delay)
            else:
                self.xaxis_log_scale(ax, min_mean_delay, max_mean_delay)
            ax.invert_xaxis()

            yticks = ax.get_yticks()
            if yticks[0] < 0:
                ax.set_ylim(bottom=0)

            xlabel = '95th percentile one-way delay (ms)'
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel('Average throughput (Mbit/s)', fontsize=12)
            ax.grid()

        # save summary
        ax_raw.set_title(self.expt_title.strip(), y=1.02, fontsize=12)
        lgd = ax_raw.legend(scatterpoints=1, bbox_to_anchor=(1, 0.5),
                            loc='center left', fontsize=12)

        for graph_format in ['svg']:
            raw_summary = path.join(
                self.data_dir, 'summary.%s' % graph_format)
            fig_raw.savefig(raw_summary, dpi=300, bbox_extra_artists=(lgd,),
                            bbox_inches='tight', pad_inches=0.2)

        # save summary_mean
        ax_mean.set_title(self.expt_title +
                          ' (mean of all runs by scheme)', fontsize=12)

        for graph_format in ['svg']:
            mean_summary = path.join(
                self.data_dir, 'summary_mean.%s' % graph_format)
            fig_mean.savefig(mean_summary, dpi=300,
                             bbox_inches='tight', pad_inches=0.2)

        sys.stderr.write(
            'Saved throughput graphs, delay graphs, and summary '
            'graphs in %s\n' % self.data_dir)


    def run(self):
        perf_data = self.eval_performance()

        data_for_plot = {}

        for cc in perf_data:
            data_for_plot[cc] = []

            for run_id in perf_data[cc]:
                if perf_data[cc][run_id] is None:
                    continue

                tput = perf_data[cc][run_id]['throughput']
                delay = perf_data[cc][run_id]['delay']
                if tput is None or delay is None:
                    continue
                data_for_plot[cc].append((tput, delay))


        self.plot_throughput_delay(data_for_plot)
        plt.close('all')

    


def main():
    args = parse_plot()
    Plot(args).run()


if __name__ == '__main__':
    main()
