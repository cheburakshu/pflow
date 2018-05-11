
class ServerState:
    '''
    States transition:
    SHUTDOWN -> STARTING
    STARTING -> RUNNING
    RUNNING -> SHUTTING DOWN
    SHUTTING_DOWN -> SHUTDOWN
    '''

    VALID_STATES = ['SHUTDOWN', 'STARTING', 'RUNNING', 'SHUTTING_DOWN', 'STANDBY', 'RESUMING', 'SUSPENDING']
    INPUTS = ['START', 'STOP', 'DONE', 'SUSPEND', 'RESUME']

    SHUTDOWN, STARTING, RUNNING, SHUTTING_DOWN, STANDBY, RESUMING, SUSPENDING = VALID_STATES

    START, STOP, DONE, SUSPEND, RESUME = INPUTS

    INITIAL_STATE = SHUTDOWN

    # Current_State, Input, Next_State
    TRUTH_TABLE = [
        [SHUTDOWN, START, STARTING], 
        [STARTING, DONE, STANDBY], 
        [STANDBY, RESUME, RUNNING], 
        [RUNNING, SUSPEND, SUSPENDING], 
        [SUSPENDING, DONE, STANDBY], 
        [STANDBY, STOP, SHUTTING_DOWN], 
        [SHUTTING_DOWN, DONE, SHUTDOWN], 
    ]

    # Command, [Current State, Target State], [State transition list] 
    TARGET_STATE_COMMANDS = [
        [[SHUTDOWN, RUNNING], [START, DONE, RESUME]], 
        [[RUNNING, SHUTDOWN], [SUSPEND, DONE, STOP, DONE]], 
        [[RUNNING, RUNNING], [SUSPEND, DONE, STOP, DONE, START, DONE, RESUME]], 
    ]

    def is_state_valid (self, state):
        return state in self.VALID_STATES 

    def is_input_valid (self, input):
        return input in self.INPUTS

    def get_next_state (self, current_state, input):
        for i in self.TRUTH_TABLE:
            if i[0] == current_state and i[1] == input:
                return i[2]
        return current_state

    def get_state_transition(self, current_state, target_state):
        for i in self.TARGET_STATE_COMMANDS:
            if [current_state, target_state] == i[0]:
                return i[1]
