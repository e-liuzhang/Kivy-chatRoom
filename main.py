import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button 
from kivy.uix.screenmanager import ScreenManager,Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
import socket_client
import os
import sys
kivy.require('1.11.1')
# 导入字体（宋体）解决kivy的中文乱码问题
# font1 = kivy.resources.resource_find("./font/simsun.ttc")
font1 = kivy.resources.resource_find("simsun.ttc")


class ScrollableLable(ScrollView):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.layout=GridLayout(cols=2,size_hint_y=None)
        self.add_widget(self.layout)

        self.chat_history=Label(size_hint_y=None,markup=True)
        self.scroll_to_point=Label()

        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)
    # 更新chat信息
    def update_chat_history(self,message):
        self.chat_history.text+='\n'+message
        # 设置chat字体
        self.chat_history.font_name=font1
        self.layout.height=self.chat_history.texture_size[1]+15
        self.chat_history.height=self.chat_history.texture_size[1]
        self.chat_history.text_size=(self.chat_history.width*0.98,None)
        self.scroll_to(self.scroll_to_point)
    # 改变窗口时更新窗口方法
    def update_chat_history_layout(self,_=None):
        self.layout.height=self.chat_history.texture_size[1]+15
        self.chat_history.height=self.chat_history.texture_size[1]
        self.chat_history.text_size=(self.chat_history.width*0.98,None)

# 连接页
class ConnectPage(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.cols= 2
# 存储输入字段信息
        if os.path.isfile("prev_details.txt"):
            with open("prev_details.txt","r") as f:
                d=f.read().split(",")
                prev_ip=d[0]
                prev_port=d[1]
                prev_username=d[2]
        else:
            prev_ip=""
            prev_port=""
            prev_username=""
# elements for page 
        self.add_widget(Label(text='IP:'))
        self.ip=TextInput(text=prev_ip,multiline=False)
        self.add_widget(self.ip)

        self.add_widget(Label(text='Port:'))
        self.port=TextInput(text=prev_port,multiline=False)
        self.add_widget(self.port)

        self.add_widget(Label(text='Username:'))
        self.username=TextInput(text=prev_username,multiline=False,font_name=font1)
        self.add_widget(self.username)
        # 添加页面跳转按钮
        self.join=Button(text="Join")
        # 添加按钮事件
        self.join.bind(on_press=self.join_button)
        self.add_widget(Label())
        self.add_widget(self.join)


    def join_button(self,instance):
        port=self.port.text
        ip=self.ip.text
        username=self.username.text
       
        with open("prev_details.txt","w") as f:
            f.write(f"{ip},{port},{username}")

        info=f"Attempting to join {ip}:{port} as {username}"
        # 将首页的info信息存入info页
        chat_app.info_page.update_info(info)
        # 跳转页面
        chat_app.screen_manager.current="Info"
        Clock.schedule_once(self.connect,1)

    def connect(self,_):
        port=int(self.port.text)
        ip=self.ip.text
        username=self.username.text

        if not socket_client.connect(ip,port,username,show_error):
            return
        chat_app.create_chat_page()
        chat_app.screen_manager.current="Chat"


class InfoPage(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        # element for page
        self.cols= 1
        self.message=Label(halign="center",valign="middle",font_size=30,font_name=font1)    
        # self.message=Label(halign="center",valign="middle",font_size=30)    
        # 绑定事件
        self.message.bind(width=self.update_text_width)
        self.add_widget(self.message)
    def update_info(self,message):
        self.message.text=message
    def update_text_width(self,*_):
        self.message.text_size=(self.message.width*0.9,None)

class ChatPage(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        # element for page
        self.cols= 1
        self.row=2
        # ScrollableLable为history（历史记录）
        self.history=ScrollableLable(height=Window.size[1]*0.9,size_hint_y=None)
        self.add_widget(self.history)
        self.new_message=TextInput(width=Window.size[0]*0.8,size_hint_x=None,multiline=False,font_name=font1)
        self.send=Button(text="Send")
        self.send.bind(on_press=self.send_message)
        
        bottom_line=GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)

        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_once(self.focus_text_input,1)
        # 监听
        socket_client.start_listening(self.incoming_message,show_error)
        #解决窗口变化问题 
        self.bind(size=self.adjust_fields)

    def adjust_fields(self,*_):
        # 控制chat界面的大小
        if Window.size[1]*0.1<50:
            new_height=Window.size[1]-50
        else:
            new_height=Window.size[1]*0.9
        self.history.height=new_height
        # 下面零件的大小
        if Window.size[0]*0.2<100:
            new_width=Window.size[0]-100
        else:
            new_width=Window.size[0]*0.8
        self.new_message.width=new_width
        #每次改变窗口都调用更新方法 
        Clock.schedule_once(self.history.update_chat_history_layout,0.01)

    def on_key_down(self,instance,keyboard,keycode,text,modifiers):
        if keyboard==40:
            self.send_message(None)
        


    def send_message(self,_):
        message=self.new_message.text
        self.new_message.text=""
        if message:
            self.history.update_chat_history(f"[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}")
            socket_client.send(message)
        Clock.schedule_once(self.focus_text_input,0.1)

    def focus_text_input(self,_):
        self.new_message.focus=True

    def incoming_message(self,username,message):
        self.history.update_chat_history(f"[color=20dd20]{username}[/color] > {message}")
        
        print("send a message!!!")


        # self.add_widget(Label(text="Hey at least it worked up to this point!!!!"))

class ChatApp(App):

    def build(self):
        # 页面控制
        self.screen_manager=ScreenManager()
        # 首页
        self.connect_page=ConnectPage()
        screen=Screen(name="Connect")
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)
        # info页
        self.info_page=InfoPage()
        screen=Screen(name="Info")
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def create_chat_page(self):
        self.chat_page=ChatPage()
        screen=Screen(name="Chat")
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)

def show_error(message):
    chat_app.info_page.update_info(message)
        # 跳转页面
    chat_app.screen_manager.current="Info"
    Clock.schedule_once(sys.exit,10)


if __name__ == '__main__':
    chat_app=ChatApp()
    chat_app.run()
