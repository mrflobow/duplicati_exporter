#!/usr/bin/env python3
import json
import os
from datetime import datetime

from prometheus_client.twisted import MetricsResource
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

from prometheus_client import Gauge, MetricsHandler, Enum



backup_started = Gauge('backup_started', 'Time when the last backup started', ['task'])
backup_duration = Gauge('backup_duration', 'Time the backup needed to complete', ['task'])
backup_ended = Gauge('backup_ended', 'Time the last backup completed', ['task'])

backup_job_size_of = Gauge('backup_job_size_of',"Represent the size of various items", ['task','type'])
backup_state = Enum('backup_state', 'Represents the backup status', states=['success', 'failed', 'warning','unknown'], labelnames=['task'])
backup_job_count = Gauge('backup_job_count','Counts of open files, added files, deleted files during the job execution',['task','type'])
backup_backend_count = Gauge('backup_backend_count','Counts of backend  added files, deleted files, created folders',['task', 'type'])
backup_local_size = Gauge('backup_local_size', 'Size of the local files for backup', ['task'])
backup_remote_size = Gauge('backup_remote_size', 'Size of the backup on remote backend', ['task'])

class CollectReport(Resource):
    def render_POST(self, request):
        report = request.content.read().decode("utf-8")
        try:
            jreport = json.loads(report)
        except ValueError:
            return "error".encode('utf8')

        backup_name = jreport['Extra']['backup-name']
        self.set_backup_state(jreport, backup_name)
        self.calc_backup_time(jreport, backup_name)
        self.collect_job_sizeof(jreport, backup_name)
        self.collect_job_count(jreport, backup_name)
        self.collect_backend_count(jreport, backup_name)
        # Local
        sof = jreport['Data']['SizeOfExaminedFiles']
        backup_local_size.labels(task=backup_name).set(sof)
        # Remote Backend
        sof = jreport['Data']['BackendStatistics']['KnownFileSize']
        backup_local_size.labels(task=backup_name).set(sof)


        print(jreport)
        print(backup_name)

        content = "Recieved"
        return content.encode("utf8")

    def set_backup_state(self,jreport,backup_name):
        main_op = jreport['Data']['MainOperation']
        state = jreport['Data']['ParsedResult']

        if main_op != "Backup":
            backup_state.labels(task=backup_name).state("unknown")
            return

        if state == "Success":
            backup_state.labels(task=backup_name).state("success")
        elif state == "Failed":
            backup_state.labels(task=backup_name).state("failed")
        elif state == "Warning":
            backup_state.labels(task=backup_name).state("warning")
        else:
            backup_state.labels(task=backup_name).state("unknown")


    def backup_time2micro(self,str_time):
        ptime = datetime.strptime(str_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        return ptime.timestamp() * 1000
    def calc_backup_time(self,jreport,backup_name):

        # Begin Time
        str_begin_time = jreport['Data']['BeginTime']
        backup_started.labels(task=backup_name).set(self.backup_time2micro(str_begin_time))

        # End Time
        str_end_time = jreport['Data']['EndTime']
        backup_ended.labels(task=backup_name).set(self.backup_time2micro(str_end_time))

        # Duration
        b_dur = jreport['Data']['Duration'][:-1]
        pt = datetime.strptime(b_dur, '%H:%M:%S.%f')
        a_timedelta = pt - datetime(1900, 1, 1)
        b_dur_sec = a_timedelta.total_seconds()
        backup_duration.labels(task=backup_name).set(b_dur_sec)


    def collect_job_sizeof(self,jreport,backup_name):
        # SizeOfExaminedFiles
        sof = jreport['Data']['SizeOfExaminedFiles']
        backup_job_size_of.labels(task=backup_name, type='exm_files').set(sof)

        # SizeOfAddedFiles
        sof = jreport['Data']['SizeOfAddedFiles']
        backup_job_size_of.labels(task=backup_name, type='added_files').set(sof)

        # SizeOfModifiedFiles
        sof = jreport['Data']['SizeOfModifiedFiles']
        backup_job_size_of.labels(task=backup_name, type='mod_files').set(sof)

        # SizeOfModifiedFiles
        sof = jreport['Data']['SizeOfModifiedFiles']
        backup_job_size_of.labels(task=backup_name, type='mod_files').set(sof)

        # SizeOfOpenedFiles
        sof = jreport['Data']['SizeOfOpenedFiles']
        backup_job_size_of.labels(task=backup_name, type='op_files').set(sof)

    def collect_job_count(self,jreport,backup_name):

        del_files = jreport['Data']['DeletedFiles']
        del_folder = jreport['Data']['DeletedFolders']
        mod_files = jreport['Data']['ModifiedFiles']
        exm_files = jreport['Data']['ExaminedFiles']
        op_files = jreport['Data']['OpenedFiles']
        add_files = jreport['Data']['AddedFiles']
        add_folders= jreport['Data']['AddedFolders']
        tol_files = jreport['Data']['TooLargeFiles']
        mod_folders = jreport['Data']['ModifiedFolders']
        mod_sym = jreport['Data']['ModifiedSymlinks']
        add_sym = jreport['Data']['AddedSymlinks']
        del_sym = jreport['Data']['DeletedSymlinks']

        backup_job_count.labels(task=backup_name,type='del_files').set(del_files)
        backup_job_count.labels(task=backup_name, type='del_folder').set(del_folder)
        backup_job_count.labels(task=backup_name, type='mod_files').set(mod_files)
        backup_job_count.labels(task=backup_name, type='exm_files').set(exm_files)
        backup_job_count.labels(task=backup_name, type='del_files').set(del_files)
        backup_job_count.labels(task=backup_name, type='op_files').set(op_files)
        backup_job_count.labels(task=backup_name, type='add_files').set(add_files)
        backup_job_count.labels(task=backup_name, type='add_folders').set(add_folders)
        backup_job_count.labels(task=backup_name, type='tol_files').set(tol_files)
        backup_job_count.labels(task=backup_name, type='mod_folders').set(mod_folders)
        backup_job_count.labels(task=backup_name, type='mod_sym').set(mod_sym)
        backup_job_count.labels(task=backup_name, type='add_sym').set(add_sym)
        backup_job_count.labels(task=backup_name, type='del_sym').set(del_sym)

    def collect_backend_count(self,jreport,backup_name):
        bs = jreport['Data']['BackendStatistics']
        files_up = bs['FilesUploaded']
        files_down = bs['FilesDownloaded']
        files_del = bs['FilesDeleted']
        folders_created = bs['FoldersCreated']
        backup_list = bs['BackupListCount']

        backup_backend_count.labels(task=backup_name, type='files_up').set(files_up)
        backup_backend_count.labels(task=backup_name, type='files_down').set(files_down)
        backup_backend_count.labels(task=backup_name, type='files_del').set(files_del)
        backup_backend_count.labels(task=backup_name, type='folders_created').set(folders_created)
        backup_backend_count.labels(task=backup_name, type='backup_list').set(backup_list)

def main():
    """Main entry point"""
    exporter_port = os.getenv("EXPORTER_PORT", "9123")
    root = Resource()
    root.putChild(b'metrics', MetricsResource())
    root.putChild(b'report', CollectReport())

    factory = Site(root)
    reactor.listenTCP(int(exporter_port), factory)
    reactor.run()

if __name__ == "__main__":
    main()