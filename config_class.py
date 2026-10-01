class Config:
    lower_bound: int
    upper_bound: int
    pause_hotkey: str
    exit_hotkey: str
    parallel_world_gen: bool
    ensure_correct_instance_retry: float
    before_switch_esc_press_pause: float
    set_up_key_press_pause: float
    DEBUG: bool

    def __init__(self, lower_bound: int, upper_bound: int, pause_hotkey: str,
                 exit_hotkey: str, parallel_world_gen: bool, ensure_correct_instance_retry: float,
                 before_switch_esc_press_pause: float, set_up_key_press_pause: float, debug: bool):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.pause_hotkey = pause_hotkey
        self.exit_hotkey = exit_hotkey
        self.parallel_world_gen = parallel_world_gen
        self.ensure_correct_instance_retry = ensure_correct_instance_retry
        self.before_switch_esc_press_pause = before_switch_esc_press_pause
        self.set_up_key_press_pause = set_up_key_press_pause
        self.DEBUG = debug

    def __eq__(self, other: object):
        return (self.lower_bound == other.lower_bound and
                self.upper_bound == other.upper_bound and
                self.pause_hotkey == other.pause_hotkey
                and self.exit_hotkey == other.exit_hotkey and
                self.parallel_world_gen == other.parallel_world_gen and
                self.ensure_correct_instance_retry == other.ensure_correct_instance_retry and
                self.before_switch_esc_press_pause == other.before_switch_esc_press_pause and
                self.set_up_key_press_pause == other.set_up_key_press_pause and self.DEBUG == other.DEBUG)