import os
# Windows audio stability
os.environ['KIVY_AUDIO'] = 'sdl2'

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from plyer import battery, notification
from datetime import datetime, timedelta
import random

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget, OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KV = '''
<DayChip@MDChip>:
    type: "filter"
    md_bg_color: 0.15, 0.15, 0.15, 1

<AlarmListItem>:
    text: root.alarm_time
    secondary_text: root.alarm_days
    IconLeftWidget:
        icon: "alarm"
    IconRightWidget:
        MDSwitch:
            active: root.is_active
            pos_hint: {'center_y': .5}
            on_active: app.toggle_alarm(root.index, self.active)

MDScreen:
    md_bg_color: 0.05, 0.05, 0.05, 1

    MDBottomNavigation:
        id: nav
        panel_color: 0.1, 0.1, 0.1, 1
        text_color_active: 0, 0.9, 1, 1

        # 1. ALARM TAB
        MDBottomNavigationItem:
            name: 'alarm_screen'
            text: 'Alarm'
            icon: 'alarm'
            MDBoxLayout:
                orientation: 'vertical'
                padding: "15dp"
                spacing: "10dp"
                
                MDCard:
                    size_hint_y: None
                    height: "100dp"
                    md_bg_color: 0.1, 0.1, 0.1, 1
                    radius: [20, ]
                    MDBoxLayout:
                        orientation: 'vertical'
                        padding: "10dp"
                        MDLabel:
                            id: live_clock
                            text: "00:00:00"
                            halign: "center"
                            font_style: "H4"
                            text_color: 0, 0.9, 1, 1
                            theme_text_color: "Custom"
                        MDLabel:
                            id: live_date
                            text: "---"
                            halign: "center"
                            theme_text_color: "Secondary"

                MDBoxLayout:
                    spacing: "10dp"
                    adaptive_height: True
                    MDTextField:
                        id: hour
                        hint_text: "HH"
                        mode: "rectangle"
                    MDTextField:
                        id: minute
                        hint_text: "MM"
                        mode: "rectangle"

                MDLabel:
                    text: "Select Recurring Days:"
                    font_style: "Caption"
                    theme_text_color: "Secondary"

                MDBoxLayout:
                    id: days_box
                    adaptive_height: True
                    spacing: "4dp"
                    DayChip:
                        text: "Mon"
                        id: mon
                    DayChip:
                        text: "Tue"
                        id: tue
                    DayChip:
                        text: "Wed"
                        id: wed
                    DayChip:
                        text: "Thu"
                        id: thu
                    DayChip:
                        text: "Fri"
                        id: fri
                    DayChip:
                        text: "Sat"
                        id: sat
                    DayChip:
                        text: "Sun"
                        id: sun

                MDRaisedButton:
                    text: "SAVE ALARM"
                    md_bg_color: 0, 0.5, 0.8, 1
                    size_hint_x: 1
                    on_release: app.add_alarm()

                MDScrollView:
                    MDList:
                        id: alarms_container

                MDIconButton:
                    icon: "stop-circle"
                    pos_hint: {"center_x": .5}
                    text_color: 1, 0.2, 0.2, 1
                    on_release: app.stop_check()

        # 2. BATTERY TAB (UI FIXED)
        MDBottomNavigationItem:
            name: 'battery_screen'
            text: 'Battery'
            icon: 'battery-flash'
            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                spacing: "20dp"
                
                MDCard:
                    orientation: 'vertical'
                    padding: "20dp"
                    spacing: "15dp"
                    md_bg_color: 0.1, 0.1, 0.1, 1
                    radius: [25, ]
                    adaptive_height: True
                    
                    MDIcon:
                        id: battery_icon
                        icon: "battery-80"
                        font_size: "100sp"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0, 1, 0.5, 1
                    
                    MDLabel:
                        id: battery_live_label
                        text: "Calculating..."
                        halign: "center"
                        font_style: "H3"
                        theme_text_color: "Primary"

                MDTextField:
                    id: battery_target
                    hint_text: "Alert at %"
                    mode: "fill"
                    input_filter: "int"
                
                MDRaisedButton:
                    id: sound_btn
                    text: "SELECT ALARM SOUND"
                    pos_hint: {"center_x": .5}
                    on_release: app.open_sound_menu()

        # 3. STOPWATCH TAB (WITH LAP)
        MDBottomNavigationItem:
            name: 'stopwatch_screen'
            text: 'Stopwatch'
            icon: 'timer'
            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                spacing: "10dp"
                MDLabel:
                    id: sw_label
                    text: "00:00.00"
                    halign: "center"
                    font_style: "H2"
                    text_color: 0, 0.9, 1, 1
                    theme_text_color: "Custom"
                MDBoxLayout:
                    spacing: "10dp"
                    adaptive_height: True
                    pos_hint: {"center_x": .5}
                    MDFillRoundFlatButton:
                        id: sw_btn
                        text: "START"
                        on_release: app.sw_start_stop()
                    MDFillRoundFlatButton:
                        text: "LAP"
                        on_release: app.sw_lap()
                    MDFillRoundFlatButton:
                        text: "RESET"
                        on_release: app.sw_reset()
                MDScrollView:
                    MDList:
                        id: lap_container
'''

from kivy.properties import StringProperty, BooleanProperty, NumericProperty

class AlarmListItem(TwoLineAvatarIconListItem):
    alarm_time = StringProperty()
    alarm_days = StringProperty()
    is_active = BooleanProperty()
    index = NumericProperty()

class AlarmApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.alarms = []
        self.alarm_sound = None
        self.preview_sound = None
        self.sound_playing = False
        self.selected_sound = "alarm_sound.wav"
        self.sw_seconds = 0
        self.sw_running = False
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_interval(self.update_all, 1)
        self.setup_menu()

    def update_all(self, dt):
        now = datetime.now()
        cur_time, cur_day = now.strftime("%H:%M"), now.strftime("%a")
        
        try:
            self.root.ids.live_clock.text = now.strftime("%H:%M:%S")
            self.root.ids.live_date.text = now.strftime("%d %B %Y")
            
            # --- BATTERY LIVE ---
            perc = battery.status.get("percentage")
            if perc is not None:
                self.root.ids.battery_live_label.text = f"{perc}%"
                icon_idx = (perc // 10) * 10
                self.root.ids.battery_icon.icon = f"battery-{icon_idx}" if 0 < icon_idx < 100 else ("battery" if icon_idx >= 100 else "battery-outline")
                self.root.ids.battery_icon.text_color = [1, 0, 0, 1] if perc <= 20 else [0, 1, 0.5, 1]
                
                bt = self.root.ids.battery_target.text
                if bt and perc >= int(bt):
                    self.play_alarm(); self.root.ids.battery_target.text = ""

            # --- ALARM CHECK ---
            for alarm in self.alarms:
                if alarm["active"] and alarm["time"] == cur_time:
                    if not alarm["days"] or cur_day in alarm["days"]:
                        self.play_alarm()
                        if not alarm["days"]: alarm["active"] = False
                        self.refresh_list()
        except: pass

    def setup_menu(self):
        files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(('.mp3', '.wav'))]
        if not files: files = ["alarm_sound.wav"]
        items = [{"viewclass": "OneLineListItem", "text": f, "on_release": lambda x=f: self.set_sound_and_preview(x)} for f in files]
        self.menu = MDDropdownMenu(caller=self.root.ids.sound_btn, items=items, width_mult=4)

    def set_sound_and_preview(self, f):
        self.selected_sound = f
        self.root.ids.sound_btn.text = f"Sound: {f}"
        self.menu.dismiss()
        if self.preview_sound: self.preview_sound.stop()
        self.preview_sound = SoundLoader.load(os.path.join(BASE_DIR, f))
        if self.preview_sound:
            self.preview_sound.play()
            Clock.schedule_once(lambda dt: self.preview_sound.stop() if self.preview_sound else None, 3)

    def add_alarm(self):
        ids = self.root.ids
        if ids.hour.text and ids.minute.text:
            t_str = f"{ids.hour.text.zfill(2)}:{ids.minute.text.zfill(2)}"
            days_map = {"mon":"Mon", "tue":"Tue", "wed":"Wed", "thu":"Thu", "fri":"Fri", "sat":"Sat", "sun":"Sun"}
            selected = [days_map[d] for d in days_map if ids[d].active]
            self.alarms.append({"time": t_str, "days": selected, "active": True})
            self.refresh_list()
            ids.hour.text = ""; ids.minute.text = ""
            for d in days_map: ids[d].active = False

    def refresh_list(self):
        container = self.root.ids.alarms_container
        container.clear_widgets()
        for i, alarm in enumerate(self.alarms):
            container.add_widget(AlarmListItem(
                alarm_time=alarm["time"],
                alarm_days=", ".join(alarm["days"]) if alarm["days"] else "Once",
                is_active=alarm["active"],
                index=i
            ))

    def toggle_alarm(self, idx, val):
        if idx < len(self.alarms): self.alarms[idx]["active"] = val

    def play_alarm(self):
        if not self.sound_playing:
            self.alarm_sound = SoundLoader.load(os.path.join(BASE_DIR, self.selected_sound))
            if self.alarm_sound:
                self.sound_playing = True
                self.alarm_sound.loop = True
                self.alarm_sound.play()

    def stop_check(self):
        if not self.sound_playing: return
        self.a, self.b = random.randint(15, 60), random.randint(15, 60)
        self.math_input = MDTextField(hint_text="Result?")
        self.dialog = MDDialog(
            title=f"Math Challenge: {self.a} + {self.b}", type="custom",
            content_cls=self.math_input,
            buttons=[MDFlatButton(text="STOP", on_release=self.verify_math)]
        )
        self.dialog.open()

    def verify_math(self, *args):
        if self.math_input.text == str(self.a + self.b):
            self.dialog.dismiss(); self.stop_alarm()

    def stop_alarm(self):
        if self.alarm_sound: self.alarm_sound.stop()
        self.sound_playing = False

    def sw_start_stop(self):
        if not self.sw_running:
            self.sw_running = True
            self.root.ids.sw_btn.text = "STOP"
            Clock.schedule_interval(self.update_sw, 0.05)
        else:
            self.sw_running = False
            self.root.ids.sw_btn.text = "START"
            Clock.unschedule(self.update_sw)

    def update_sw(self, dt):
        self.sw_seconds += dt
        mins, secs = divmod(self.sw_seconds, 60)
        self.root.ids.sw_label.text = f"{int(mins):02d}:{int(secs):02d}.{int((secs%1)*100):02d}"

    def sw_lap(self):
        if self.sw_seconds > 0:
            self.root.ids.lap_container.add_widget(OneLineListItem(text=f"Lap: {self.root.ids.sw_label.text}"))

    def sw_reset(self):
        self.sw_running = False
        Clock.unschedule(self.update_sw)
        self.sw_seconds = 0
        self.root.ids.sw_label.text = "00:00.00"
        self.root.ids.lap_container.clear_widgets()

    def open_sound_menu(self): self.menu.open()

if __name__ == "__main__":
    AlarmApp().run()