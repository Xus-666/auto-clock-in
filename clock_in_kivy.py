"""
自动打卡工具 - Android APP (Kivy版)
使用 Kivy 框架，支持 Android APK 打包
"""
import requests
import random
from datetime import datetime

import kivy
kivy.require("2.2.0")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase

# 注册中文字体（如果没有系统字体，就用默认）
try:
    LabelBase.register(name="Sans", fn_regular="/system/fonts/DroidSansFallback.ttf")
except Exception:
    pass


class AutoClockIn:
    """打卡核心类"""

    def __init__(self, token: str):
        self.base_url = "https://hbgj.njuae.cn/base-business-api/api"
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.47"
        })

        self.LOCATIONS = {
            "兴化": {
                "longitude_range": (119.849000, 119.850000),
                "latitude_range": (32.940500, 32.941500),
                "address": "兴化市生态环境局"
            },
            "南大": {
                "longitude": "118.776441",
                "latitude": "32.058625",
                "address": "南京大学科学楼"
            }
        }

    def _randomize_location(self, location_config: dict) -> dict:
        if "longitude_range" in location_config:
            lng_min, lng_max = location_config["longitude_range"]
            lat_min, lat_max = location_config["latitude_range"]
            return {
                "longitude": str(round(random.uniform(lng_min, lng_max), 6)),
                "latitude": str(round(random.uniform(lat_min, lat_max), 6)),
                "address": location_config["address"]
            }
        return {
            "longitude": location_config["longitude"],
            "latitude": location_config["latitude"],
            "address": location_config["address"]
        }

    def clock_in(self, location: str, clock_type: str) -> dict:
        loc_config = self.LOCATIONS.get(location, self.LOCATIONS["兴化"])
        loc = self._randomize_location(loc_config)

        data = {
            "clockLongitude": loc["longitude"],
            "clockLatitude": loc["latitude"],
            "clockAddress": loc["address"],
            "clockType": clock_type
        }

        url = f"{self.base_url}/auth/b/clock"
        response = self.session.post(url, json=data)
        try:
            return response.json()
        except Exception:
            return {"error": str(response.text)}


# ── Kivy GUI ────────────────────────────────────────────────────────────────

class ClockInLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 12
        self.clock_in_obj = None  # 延迟初始化

        # 标题
        header = BoxLayout(size_hint_y=None, height=60)
        header_bg = BoxLayout(pos=header.pos, size=header.size)
        with header_bg.canvas.before:
            Color(0.086, 0.467, 1.0, 1)  # #1677ff
            Rectangle(pos=header.pos, size=header.size)
        title_label = Label(
            text="[b]📋 自动打卡工具[/b]",
            font_size="20sp", markup=True,
            halign="center", valign="middle",
            color=(1, 1, 1, 1)
        )
        header.add_widget(title_label)
        self.add_widget(header)

        # 表单区域
        form = StackLayout(size_hint_y=None, spacing=8)
        form.bind(minimum_height=form.setter("height"))

        # 授权码
        form.add_widget(Label(
            text="授权码 (TOKEN)", font_size="14sp",
            size_hint_y=None, height=32, halign="left",
            text_size=(Window.size[0] - 40, 32)
        ))
        self.token_input = TextInput(
            hint_text="请输入授权码TOKEN", multiline=False,
            font_size="14sp", size_hint_y=None, height=48,
            padding=[12, 12], background_normal="",
            foreground_color=(0, 0, 0, 1)
        )
        form.add_widget(self.token_input)

        # 位置选择
        form.add_widget(Label(
            text="打卡位置", font_size="14sp",
            size_hint_y=None, height=32, halign="left",
            text_size=(Window.size[0] - 40, 32)
        ))
        self.location_spinner = Spinner(
            text="兴化",
            values=["兴化", "南大"],
            font_size="14sp", size_hint_y=None, height=48,
            background_normal="", background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            sync_height=True
        )
        form.add_widget(self.location_spinner)

        # 打卡状态
        form.add_widget(Label(
            text="打卡状态", font_size="14sp",
            size_hint_y=None, height=32, halign="left",
            text_size=(Window.size[0] - 40, 32)
        ))
        self.type_spinner = Spinner(
            text="上班 (1)",
            values=["上班 (1)", "下班 (2)"],
            font_size="14sp", size_hint_y=None, height=48,
            background_normal="", background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            sync_height=True
        )
        form.add_widget(self.type_spinner)

        self.add_widget(form)

        # 提交按钮
        self.submit_btn = Button(
            text="提 交 打 卡",
            font_size="16sp", bold=True,
            background_color=(0.086, 0.467, 1.0, 1),
            size_hint_y=None, height=56,
            background_normal="", background_down=""
        )
        self.submit_btn.bind(on_press=self.do_submit)
        self.add_widget(self.submit_btn)

        # 结果文本区
        self.result_label = Label(
            text="等待提交…",
            font_size="13sp", halign="left", valign="top",
            text_size=(Window.size[0] - 48, None),
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None, height=100
        )
        self.add_widget(self.result_label)

        # 版本信息
        ver_label = Label(
            text="v1.0 · 仅供学习交流", font_size="11sp",
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None, height=24
        )
        self.add_widget(ver_label)

    def _validate(self):
        """校验参数"""
        errors = []
        if not self.token_input.text.strip():
            errors.append("授权码 (TOKEN)")
        if not self.location_spinner.text.strip():
            errors.append("打卡位置")
        if not self.type_spinner.text.strip():
            errors.append("打卡状态")
        return errors

    def do_submit(self, instance):
        errors = self._validate()
        if errors:
            self._show_popup("缺少参数", f"请填写以下内容：\n" + "\n".join(f"• {e}" for e in errors))
            return

        token = self.token_input.text.strip()
        location = self.location_spinner.text
        clock_type = "1" if "上班" in self.type_spinner.text else "2"

        self.submit_btn.text = "提交中…"
        self.submit_btn.disabled = True
        self.result_label.text = f"[{datetime.now().strftime('%H:%M:%S')}] 正在提交打卡…"

        try:
            self.clock_in_obj = AutoClockIn(token)
            resp = self.clock_in_obj.clock_in(location=location, clock_type=clock_type)

            code = resp.get("code", resp.get("status", "unknown"))
            body = resp.get("body", resp.get("data", resp))
            msg = resp.get("message", "")
            success = resp.get("success", False)  
            if success or code == 200 or code == "200":
                type_text = "上班打卡" if clock_type == "1" else "下班打卡"
                self.result_label.text = (
                    f"✅ 打卡成功！\n"
                    f"📍 位置：{location}\n"
                    f"🔖 状态：{type_text}\n"
                    f"⏰ 时间：{datetime.now().strftime('%H:%M:%S')}"
                )
                self.result_label.color = (0.0, 0.6, 0.0, 1)
                self._show_popup("打卡成功", f"✅ {location} {type_text}成功！")
            else:
                self.result_label.text = f"❌ 打卡失败\n📨 原因：{msg or str(resp)}"
                self.result_label.color = (1.0, 0.2, 0.2, 1)
                self._show_popup("打卡失败", f"❌ {msg or '未知错误'}")

        except Exception as e:
            self.result_label.text = f"❌ 网络异常：{e}"
            self.result_label.color = (1.0, 0.2, 0.2, 1)
            self._show_popup("网络异常", str(e))

        finally:
            self.submit_btn.text = "提 交 打 卡"
            self.submit_btn.disabled = False

    def _show_popup(self, title, content):
        popup = Popup(
            title=title,
            content=Label(text=content, text_size=(280, None), valign="top"),
            size_hint=(0.85, 0.4),
            background_color=(1, 1, 1, 1),
            title_color=(0, 0, 0, 1),
            title_size="16sp"
        )
        popup.open()


class ClockInApp(App):
    def build(self):
        Window.clearcolor = (0.94, 0.94, 0.96, 1)
        return ClockInLayout()


if __name__ == "__main__":
    ClockInApp().run()
