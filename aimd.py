import sys
import portus
import time
import traceback

class AIMDFlow():
    INIT_CWND = 10

    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info
        self.init_cwnd = float(self.datapath_info.mss * AIMDFlow.INIT_CWND)
        self.cwnd = self.init_cwnd
        self.datapath.set_program("default", [("Cwnd", int(self.cwnd))])

    def on_report(self, r):
        try:
            #       print("now={} bif= {} outgoing_rate={} rtt={} min_rtt={}".format(time.time(), r.inflight, r.rate, r.rtt, r.min_rtt))
            print("now={} bif= {} rtt={} ".format(round(time.time() * 1000), r.pkts_inflight, r.rtt))
            print("rate={}".format(r.rate))
            if r.loss > 0 or r.sacked > 0:
                self.cwnd /= 2
            else:
                self.cwnd += (self.datapath_info.mss * (r.acked / self.cwnd))
                self.cwnd = max(self.cwnd, self.init_cwnd)
            self.datapath.update_field("Cwnd", int(self.cwnd))

        except Exception:
            print(traceback.format_exc())
            

                
class AIMD(portus.AlgBase):

    def datapath_programs(self):
        return {
                "default" : """\
                (def (Report
                    (volatile acked 0) 
                    (volatile sacked 0) 
                    (volatile loss 0) 
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile pkts_inflight 0)
                    (volatile rate 0)
                    (volatile min_rtt 0)
                ))
                (when true 
                    (:= Report.bytes_inflight Flow.bytes_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.min_rtt (min Report.min_rtt Flow.rtt_sample_us))
                    (:= Report.rate (max Report.rate Flow.rate_outgoing))
                    (fallthrough)
                )
                (when (> Micros Flow.rtt_sample_us)
                    (report)
                    (:= Micros 0)
                )
            """
        }

    def new_flow(self, datapath, datapath_info):
        return AIMDFlow(datapath, datapath_info)

alg = AIMD()

portus.start("netlink", alg, debug=True)

