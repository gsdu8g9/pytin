# coding=utf-8
from __future__ import unicode_literals

from celery import Celery

from assets.models import Server
from cloud.provisioning import HypervisorBackend, CloudTask
from cloud.provisioning.schedulers import RatingBasedScheduler
from cmdb.settings import logger, PROXMOX_BACKEND

agentd_proxy = Celery('agentd',
                      broker=PROXMOX_BACKEND['MSG_BROKER'],
                      backend=PROXMOX_BACKEND['MSG_BACKEND'])

agentd_proxy.conf.update(
        CELERY_TASK_SERIALIZER='json',
        CELERY_RESULT_SERIALIZER='json',
        CELERY_ACCEPT_CONTENT=['json'],
        CELERY_TIMEZONE='Europe/Moscow',
        CELERY_ENABLE_UTC=True
)


class VpsControlTask(CloudTask):
    """
    Basic implementation of the VPS control task. Derived classes must define task_name property
    along with the specific agent task logic.
    """

    # Remote interface used to execute tasks
    REMOTE_WORKER = agentd_proxy
    task_name = ''

    def __init__(self, tracker, **context):
        super(VpsControlTask, self).__init__(tracker, **context)

        assert tracker
        assert self.task_name, "Set task_name property for the class."
        assert 'queue' in context

        self.queue = context['queue']

    def execute(self):
        self.context['options']['tracker_id'] = self.tracker.id

        logger.info("Executing task %s with tracker id %s" % (self.task_name, self.tracker.id))

        async_task = self.REMOTE_WORKER.send_task(self.task_name,
                                                  queue=self.queue,
                                                  routing_key=self.queue,
                                                  kwargs={'options': self.context['options']})

        logger.info("    got Celery ID %s" % async_task.id)

        tracker_context = self.tracker.context
        tracker_context['celery_task_id'] = async_task.id
        self.tracker.context = tracker_context
        self.tracker.save()

    def _get_async_task(self):
        assert 'celery_task_id' in self.tracker.context

        ctask_id = self.tracker.context['celery_task_id']
        return self.REMOTE_WORKER.AsyncResult(ctask_id)

    def poll(self):
        """
        Check task state.
        :return: Tuple (ready, result/progress info)
        """
        async_task = self._get_async_task()

        if async_task.ready():
            return True, async_task.get()

        return False, async_task.info.get('stdout', '') if async_task.info else ''


class VpsCreateTask(VpsControlTask):
    task_name = 'tasks.async.vps_create'


class VpsStartTask(VpsControlTask):
    task_name = 'tasks.async.vps_start'


class VpsStopTask(VpsControlTask):
    task_name = 'tasks.async.vps_stop'


class ProxMoxJBONServiceBackend(HypervisorBackend):
    """
    Just bunch of ProxMox nodes.
    Every node have a pytin-agentd-hv running. When task is submitted to this backend it is actually submitted
    to run remotely on the specific agent. Node to create VPS is selected by the scheduler.

    Every hypervisor node in CMDB must have options:
        role = hypervisor.
        hypervisor_driver (kvm, openvz, etc).
        agentd_taskqueue: task queue used to feed the specific agent.
        agentd_heartbeat: last heartbeat time.
    """

    TASK_CREATE = VpsCreateTask
    TASK_START = VpsStartTask
    TASK_STOP = VpsStopTask

    def __init__(self, cloud):
        super(ProxMoxJBONServiceBackend, self).__init__(cloud)

        self.scheduler = RatingBasedScheduler()

    def start_vps(self, **options):
        assert 'vmid' in options
        assert 'node' in options and options['node'] > 0

        target_node = Server.active.get(pk=options['node'])

        return self.internal_send_task(self.TASK_START, target_node, **options)

    def stop_vps(self, **options):
        assert 'vmid' in options
        assert 'node' in options and options['node'] > 0

        target_node = Server.active.get(pk=options['node'])

        return self.internal_send_task(self.TASK_STOP, target_node, **options)

    def create_vps(self, **options):
        """
        Create VPS using options.
        Parameters:
            vmid: ID of the VPS
            cpu: number of CPU cores
            ram: amount of RAM in Mb
            hdd: amount of HDD space in Gb
            user: user name
            template: template name used to create VPS.
                      It is in form: <driver>.param1.param2..paramN (kvm.centos.6.x86_64.directadmin)
                        driver: method of provisioning. Different drivers supports
                                different templates and provisioning depth.
                                Drivers can work with different virtualization technologies.

        Optional:
            node: ID of the hypervisor node. If not specified, scheduler is used to select the best node,
                     based on template.

        Populated parameters:
            hostname: hostname of the virtual machine
            driver: used driver to control the VPS (got from the template string)
            ip, gateway, netmask, dns1, dns2: network interface config

        :param options: Options used to create VPS.
        :return: TaskTracker instance to chesk progress.
        """
        assert 'vmid' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options
        assert 'template' in options

        logger.debug(options)

        if 'node' in options and options['node'] > 0:
            target_node = Server.active.get(pk=options['node'])
            hyper_driver = target_node.get_option_value('hypervisor_driver', default='unknown')
        else:
            (hyper_driver, tpl) = options['template'].split('.', 1)
            target_node = self.scheduler.get_best_node(self.cloud.get_hypervisors(hypervisor_driver=hyper_driver))

        ip, gateway, netmask = self.lease_ip(target_node.id)

        # update some options
        options['driver'] = hyper_driver
        options['hostname'] = "v%s.%s.pytin" % (options['vmid'], hyper_driver)
        options['dns1'] = '46.17.46.200'
        options['dns2'] = '46.17.40.200'
        options['ip'] = ip
        options['gateway'] = gateway
        options['netmask'] = netmask

        return self.internal_send_task(self.TASK_CREATE, target_node, **options)

    def internal_send_task(self, task_class, target_node, **task_options):
        """
        Run specific task remotely. Used to collect and send task with options to the
        remote node (worker).

        :param task_class: Task to run.
        :param target_node: Node that is used to run the task.
        :param task_options: Task options (context).
        :return: TaskTracker
        """
        assert target_node

        node_queue = target_node.get_option_value('agentd_taskqueue', default=None)
        if not node_queue:
            raise ValueError("Missing agentd_taskqueue in node %s" % target_node.id)

        logger.info("Send task %s to queue %s for node %s" % (task_class, node_queue, target_node.id))

        task_options['node'] = target_node.id
        task_options['driver'] = target_node.get_option_value('hypervisor_driver', default='unknown')

        return self.send_task(task_class,
                              cmdb_node_id=target_node.id,
                              queue=node_queue,
                              options=task_options)
