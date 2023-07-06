#!/usr/bin/env python3

import os
import taskcluster as tc
import asyncio

from nio import AsyncClientConfig, AsyncClient, MatrixRoom, RoomMessageText



class Push:
    COMM_CENTRAL = 'comm-central'
    COMM_BETA    = 'comm-beta'
    COMM_ESR115  = 'comm-esr115'
    
    TEST_SYMBOLS = [
        'GTest-1proc',
        'M',
        'M-msix',
        'X',
        'X-msix'
    ]
    
    def __init__(self, index, queue, repo, decision_id = None):
        self.index = index
        self.queue = queue
        self.repo  = repo
        
        if decision_id:
            self.decision_id = decision_id
        else:
            self.decision_id = index.findTask('comm.v2.' + self.repo + '.latest.taskgraph.decision')['taskId']
        
        self.update_tasks()

    def get_task_group(self, group_id):
        res = queue.listTaskGroup(group_id)

        tasks = []
        tasks.extend(res['tasks'])

        while 'continuationToken' in res.keys():
            res = self.queue.listTaskGroup(
                group_id,
                query = {
                    'continuationToken': res['continuationToken']
                }
            )
            tasks.extend(res['tasks'])

        return tasks
        
    def get_stripped_tasks(self, symbols, exclude_symbols = True):
        stripped_tasks = []

        for task in self.tasks:
            if exclude_symbols == True:
                if(
                    'treeherder' not in task['task']['extra'] or
                    'groupSymbol' not in task['task']['extra']['treeherder'] or
                    (
                        task['task']['extra']['treeherder']['symbol'] not in symbols and
                        task['task']['extra']['treeherder']['groupSymbol'] not in symbols
                    )
                ):
                    stripped_tasks.append(task)
            else:
                if(
                    'treeherder' in task['task']['extra'] and
                    'groupSymbol' in task['task']['extra']['treeherder'] and
                    (
                        task['task']['extra']['treeherder']['symbol'] in symbols or
                        task['task']['extra']['treeherder']['groupSymbol'] in symbols
                    )
                ):
                    stripped_tasks.append(task)

        return stripped_tasks

    def update_tasks(self):
        decision_task = self.queue.task(self.decision_id)
        push_revision = decision_task['payload']['env']['COMM_HEAD_REV']
        
        # Retrieve any special decision tasks
        decisions = self.index.listTasks('comm.v2.' + self.repo + '.revision.' + push_revision + '.taskgraph')['tasks']

        # Retrieve action tasks
        actions = self.index.listTasks('comm.v2.' + self.repo + '.revision.' + push_revision + '.taskgraph.actions')['tasks']

        # Compile task group IDs
        group_ids = []
        group_ids.extend([decision['taskId'] for decision in decisions])
        group_ids.extend([action['taskId'] for action in actions])
        #group_ids.extend([self.decision_id])

        # Retrieve tasks from each task group
        self.tasks = []
        for id in group_ids:
            self.tasks.extend(self.get_task_group(id))
        print(group_ids)
    
    def has_build_failed(self):
        failure_reasons = [
            'failed',
            'malformed-payload',
            'internal-error'
        ]
        failed_tasks = []
        
        stripped_tasks = self.get_stripped_tasks(self.TEST_SYMBOLS)
            
        for task in stripped_tasks:
            if(task['status']['runs'][-1]['reasonResolved'] in failure_reasons):
                #print(task['status']['taskId'][:], task['status']['runs'][-1]['reasonResolved'])
                #failed_tasks.append(task)
                return True

        #print(len(failed_tasks), 'failed tasks')
        return False
        
    def percent_tests_failed(self):
        failure_reasons = [
            'failed',
            'malformed-payload',
            'internal-error'
        ]
        failed_tasks = []
        
        stripped_tasks = self.get_stripped_tasks(self.TEST_SYMBOLS, False)
            
        for task in stripped_tasks:
            if(task['status']['runs'][-1]['reasonResolved'] in failure_reasons):
                #print(task['status']['taskId'][:], task['status']['runs'][-1]['reasonResolved'])
                failed_tasks.append(task)
                #return True

        #print(len(failed_tasks), 'failed tasks')
        print(len(failed_tasks) / len(stripped_tasks))
        return len(failed_tasks) / len(stripped_tasks)
            

    def rekick_problem_groups(self):
        problem_symbols = ['L10n', 'L10n-Rpk', 'MSI']
        failed_tasks = []
        
        for task in push_tasks:

            if(
                'treeherder' in task['task']['extra'] and
                'groupSymbol' in task['task']['extra']['treeherder'] and
                task['task']['extra']['treeherder']['groupSymbol'] in problem_symbols and
                task['status']['runs'][0]['reasonResolved'] == 'failed'
            ):
                print(task['status']['taskId'])
                failed_tasks.append(task)

            print(len(failed_tasks), 'failed tasks')



async def main() -> None:
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=False,
    )
    
    client = AsyncClient('https://chat.mozilla.org', config=client_config)
    #client.add_event_callback(message_callback, RoomMessageText)
    
    client.access_token = ''
    client.user_id      = '@tbbm:mozilla.org'
    client.device_id    = 'tbbm-script'
    client.load_store()

    #print(await client.login('@tbbm:mozilla.org'))
    # "Logged in as @alice:example.org device id: RANDOMDID"

    # If you made a new room and haven't joined as that user, you can use
    #await client.join("bot-test")
    print(await client.sync(30000))
    print(await client.joined_rooms())
    print(await client.room_send(
        room_id      = "!bot-test:mozilla.org",
        message_type = "m.room.message",
        content      = {
            "msgtype": "m.text",
            "body": "Hello world!"
        }
    ))
    await client.sync_forever(timeout=30000)  # milliseconds
    #await client.close()
    
    
    
asyncio.run(main())
exit()

index = tc.Index(tc.optionsFromEnvironment())
queue = tc.Queue(tc.optionsFromEnvironment())

#decision_id = index.findTask('comm.v2.comm-beta.latest.taskgraph.decision')['taskId']
#push = Push(index, queue, 'STaj3stuQeKzi1-4oVkCMw')
#push = Push(index, queue, Push.COMM_CENTRAL, 'Q9uk6CpwRtmvWzL6ovCOXA') # Failed build
push = Push(index, queue, Push.COMM_CENTRAL, 'EI8hNAeVTaqsts9ndzMAvg') # Failed tests

print(push.has_build_failed())
push.percent_tests_failed()
#print(decision_id)

#push_tasks = get_push_tasks(decision_id)

#decision_task = queue.status(decision_id)
#print(decision_task['state'])
