import json
from datetime import datetime

from prometheus_client.twisted import MetricsResource
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

from prometheus_client import Gauge, MetricsHandler

exporter_port = 80


backup_duration = Gauge('backup_duration', 'Time the Backup needed to complete', ['job'])
backup_deleted_files = Gauge('backup_deleted_files', 'Deleted files during the Backup', ['job'])
backup_size_of = Gauge('backup_size_of',"Represent the size of various items", ['job','type'])

class CollectReport(Resource):
    def render_POST(self, request):
        report = request.content.read().decode("utf-8")
        jreport = json.loads(report)
        backup_name = jreport['Extra']['backup-name']

        #Duration
        b_dur = jreport['Data']['Duration'][:-1]
        pt = datetime.strptime(b_dur, '%H:%M:%S.%f')
        a_timedelta = pt - datetime(1900, 1, 1)
        b_dur_sec = a_timedelta.total_seconds()

        #Deleted Files
        b_del_files = jreport['Data']['DeletedFiles']

        backup_duration.labels(job=backup_name).set(b_dur_sec)
        backup_deleted_files.labels(job=backup_name).set(b_del_files)

        #SizeOfExaminedFiles
        so_exfiles = jreport['Data']['SizeOfExaminedFiles']
        backup_size_of.labels(job=backup_name, type='examined_files').set(so_exfiles)

        # SizeOfAddedFiles
        so_addfiles = jreport['Data']['SizeOfAddedFiles']
        backup_size_of.labels(job=backup_name, type='added_files').set(so_addfiles)

        print(jreport)
        print(backup_name)

        content = "Recieved"
        return content.encode("ascii")


def main():
    """Main entry point"""

    root = Resource()
    root.putChild(b'metrics', MetricsResource())
    root.putChild(b'report', CollectReport())

    factory = Site(root)
    reactor.listenTCP(8000, factory)
    reactor.run()

if __name__ == "__main__":
    main()