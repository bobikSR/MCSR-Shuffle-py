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