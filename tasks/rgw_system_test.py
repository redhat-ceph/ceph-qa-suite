import yaml
import contextlib
import logging
from teuthology import misc as teuthology
from teuthology.orchestra import run
log = logging.getLogger(__name__)


class Test(object):

    def __init__(self, script_name, configuration, port_number=None):
        self.script_fname = script_name + ".py"
        self.yaml_fname = script_name + ".yaml"
        self.configuration = configuration
        # self.port_number = port_number

    def execution(self, clients):

        log.info('test: %s' % self.script_fname)

        if self.configuration is None:
            assert isinstance(self.configuration, dict), "configuration not given"
        clients[0].run(args=['sudo', 'rm', '-f', run.Raw('/tmp/*')],
                       check_status=False)
        data = self.configuration

        log.info('creating yaml from the config: %s' % data)
        local_file = '/tmp/' + self.yaml_fname
        with open(local_file,  'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))

        log.info('copying yaml to the client node')
        destination_location = \
            'rgw-tests/ceph-qe-scripts/rgw/tests/s3/yamls/' + self.yaml_fname
        clients[0].put_file(local_file,  destination_location)
        clients[0].run(args=['ls', '-lt',
                             'rgw-tests/ceph-qe-scripts/rgw/tests/s3/yamls/'])
        clients[0].run(args=['cat',
                             'rgw-tests/ceph-qe-scripts/rgw/tests/s3/yamls/' + self.yaml_fname])
        clients[0].run(
            args=[
                run.Raw(
                    'sudo venv/bin/python2.7 rgw-tests/ceph-qe-scripts/rgw/tests/s3/%s '
                    '-c rgw-tests/ceph-qe-scripts/rgw/tests/s3/yamls/%s ' % (self.script_fname, self.yaml_fname))])


def test_exec(config, data, clients):

    assert data is not None, "Got no test in configuration"

    log.info('test name :%s' % config['test-name'])

    script_name = config['test-name']
    # port_number = config['port_number']

    test = Test(script_name, data)
    test.execution(clients)


@contextlib.contextmanager
def task(ctx, config):
    """

    tasks:
    - rgw-system-test:
        test-name: test_Mbuckets
        config:
            user_count: 3
            bucket_count: 5

    tasks:
    - rgw-system-test:
        test-name: test_Mbuckets_with_Nobjects
        config:
            user_count: 3
            bucket_count: 5
            objects_count: 5
            min_file_size: 5
            max_file_size: 10

    tasks:
    - rgw-system-test:
        test-name: test_bucket_with_delete
        config:
            user_count: 3
            bucket_count: 5
            objects_count: 5
            min_file_size: 5
            max_file_size: 10


    tasks:
    - rgw-system-test:
       test-name: test_multipart_upload
       config:
           user_count: 3
           bucket_count: 5
           min_file_size: 5
           max_file_size: 10

    tasks:
    - rgw-system-test:
       test-name: test_multipart_upload_download
       config:
           user_count: 3
           bucket_count: 5
           min_file_size: 5


    tasks:
    - rgw-system-test:
       test-name: test_multipart_upload_cancel
       config:
           user_count: 3
           bucket_count: 5
           break_at_part_no: 90
           min_file_size: 1500
           max_file_size: 1000

    tasks:
    - rgw-system-test:
       test-name: test_basic_versioning
       config:
           user_count: 3
           bucket_count: 5
           objects_count: 90
           version_count: 5
           min_file_size: 1000
           max_file_size: 1500


    tasks:
    - rgw-system-test:
       test-name: test_delete_key_versions
       config:
            user_count: 3
            bucket_count: 5
            objects_count: 90
            version_count: 5
            min_file_size: 1000
            max_file_size: 1500

    tasks:
    - rgw-system-test:
       test-name: test_suspend_versioning
       config:
           user_count: 3
           bucket_count: 5
           objects_count: 90
           version_count: 5
           min_file_size: 1000
           max_file_size: 1500


    tasks:
    - rgw-system-test:
       test-name: test_version_with_revert
       config:
           user_count: 3
           bucket_count: 5
           objects_count: 90
           version_count: 5
           min_file_size: 1000
           max_file_size: 1500


    tasks:
    - rgw-system-test:
       test-name: test_acls
       config:
           bucket_count: 5
           objects_count: 90
           min_file_size: 1000
           max_file_size: 1500


    tasks:
    - rgw-system-test:
       test-name: test_acls_all_usrs
       config:
           bucket_count: 5
           user_count: 3
           objects_count: 90
           min_file_size: 1000
           max_file_size: 1500

    tasks:
    - rgw-system-test:
       test-name: test_acls_copy_obj
       config:
           objects_count: 90
           min_file_size: 1000
           max_file_size: 1500


    tasks:
    - rgw-system-test:
       test-name: test_acls_reset
       config:
           bucket_count: 5
           user_count: 3
           objects_count: 90
           min_file_size: 1000
           max_file_size: 1500


    """

    log.info('starting the task')

    log.info('config %s' % config)

    if config is None:
        config = {}

    assert isinstance(config, dict), \
        "task set-repo only supports a dictionary for configuration"

    remotes = ctx.cluster.only(teuthology.is_type('client'))
    clients = [
        remote for remote,
        roles_for_host in remotes.remotes.iteritems()]

    log.info('cloning the repo to client.0 machines')

    clients[0].run(args=['sudo', 'rm', '-rf', 'rgw-tests'], check_status=False)
    clients[0].run(args=['mkdir', 'rgw-tests'])
    clients[0].run(
        args=[
            'cd',
            'rgw-tests',
            run.Raw(';'),
            'git',
            'clone',
            'http://gitlab.osas.lab.eng.rdu2.redhat.com/ceph/ceph-qe-scripts.git',
            ])

    clients[0].run(args=['virtualenv', 'venv'])
    clients[0].run(
        args=[
            'source',
            'venv/bin/activate',
            run.Raw(';'),
            run.Raw('pip install boto names PyYaml ConfigParser'),
            run.Raw(';'),
            'deactivate'])

    config['port_number'] = '8080'
    test_config = config['config']

    # basic Upload

    data = None

    if config['test-name'] == 'test_Mbuckets':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                objects_count=0,

            )
        )

    if config['test-name'] == 'test_Mbuckets_with_Nobjects':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_Mbuckets_with_Nobjects_shards':

        # changing the value of config['test-name'] to take test_Mbuckets_with_Nobjects,
        # since this test also takes the following configuration

        config['test-name'] = 'test_Mbuckets_with_Nobjects'

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                shards=test_config['shards'],
                max_objects=test_config['max_objects'],
                bucket_count=test_config['bucket_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_bucket_with_delete':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    # multipart

    if config['test-name'] == 'test_multipart_upload':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_multipart_upload_download':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_multipart_upload_cancel':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                break_at_part_no=test_config['break_at_part_no'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    # Versioning

    if config['test-name'] == 'test_basic_versioning':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                version_count=test_config['version_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_delete_key_versions':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                version_count=test_config['version_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_suspend_versioning':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                version_count=test_config['version_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_version_with_revert':

        data = dict(
            config=dict(
                user_count=test_config['user_count'],
                bucket_count=test_config['bucket_count'],
                version_count=test_config['version_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    # ACLs

    if config['test-name'] == 'test_acls':

        data = dict(
            config=dict(
                bucket_count=test_config['bucket_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_acls_all_usrs':

        data = dict(
            config=dict(
                bucket_count=test_config['bucket_count'],
                user_count=test_config['user_count'],
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_acls_copy_obj':

        data = dict(
            config=dict(
                objects_count=test_config['objects_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    if config['test-name'] == 'test_acls_reset':

        data = dict(
            config=dict(
                objects_count=test_config['objects_count'],
                bucket_count=test_config['bucket_count'],
                user_count=test_config['user_count'],
                objects_size_range=dict(
                    min=test_config['min_file_size'],
                    max=test_config['max_file_size']
                )

            )
        )

    test_exec(config, data, clients)

    try:
        yield
    finally:

        clients[0].run(
            args=[
                'source',
                'venv/bin/activate',
                run.Raw(';'),
                run.Raw('pip uninstall boto names PyYaml -y'),
                run.Raw(';'),
                'deactivate'])

        log.info('test completed')

        log.info("Deleting repos")

        clients[0].run(args=[run.Raw(
            'sudo rm -rf venv rgw-tests *.json Download.* Download *.mpFile  x* key.*  Mp.* *.key.*')])
