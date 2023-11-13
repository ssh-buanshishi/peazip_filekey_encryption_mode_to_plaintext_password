# -*- coding: UTF-8 -*-

#Compiled On:                   VMware Workstation 15 Pro (15.5.6 build-16341506)
#Client Operating System:       Windows 7 32bit [6.1.7601]
#Python Version:                python 3.8.6(32bit)
#Pyinstaller Version:           5.13.0

#Command:                       pyinstaller -D -w --add-data "PeaZip_app.ico;." --debug noarchive --icon "PeaZip_app.ico" "main.py"


import os,sys
import hashlib
import base64
import win32clipboard as wcb
import win32con
import threading
import multiprocessing

from ui import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QObject,pyqtSignal




#存放最终输出结果，设置成全局，方便调用
_result_password_ = ""

#用来存放文件处理记录（文件路径，文件部分对应的密钥）
_file_path_record_ = []
_file_result_record_ =[]

#存放处理记录的当前索引位置
_index_ = 0

#是否正在处理
_processing_ = False




#计算sha256，推算出结果的进程函数
def calc_process(file_path:str) -> str:
    #获取文件的sha256校验值（字符串）
    h = hashlib.sha256()
    f = open(file_path, 'rb')
    while b := f.read(8192):
        h.update(b)
    f.close()
    sha256_chars    = h.hexdigest()

    #把sha256校验值字符串看成十六进制的字节串（每两个字符为一个字节，就类似winhex显示的那样）进行转换
    hex_bytes       = bytes.fromhex(sha256_chars)
            
    #把转换后的bytes编码成base64的bytes
    base64_bytes    = base64.b64encode(hex_bytes)

    #解码为字符串
    base64_string   = base64_bytes.decode(encoding="utf-8")

    return base64_string


#用来创建进程并等待结果返回的线程函数
def calc_thread(file_path:str,added_password:str) -> None:
    global _result_password_ , _file_path_record_ , _file_result_record_

    #防止意外
    if len(_file_path_record_) != len(_file_result_record_):
        _file_path_record_.clear()
        _file_result_record_.clear()

    path_is_file = os.path.isfile(file_path)
    #判断路径是否存在
    if path_is_file:
        #查看文件是否在之前处理过，毕竟对于大文件来说计算sha256需要很长时间，
        #如果文件有生成记录，下面的密码手抖输错，再按一次生成时，直接查数据更快
        try:
            index_local = _file_path_record_.index(file_path)
        except:
            #判断文件是否大于20MB
            if ((os.path.getsize(file_path)) > 20971520):#1024*1024*20（20MB）
                
                ret_value = []

                #创建进程，在进程里计算，线程负责接收返回值
                pool = multiprocessing.Pool(processes=1)#只有一个任务，只需要一个进程
                r = pool.apply_async(calc_process, (file_path,), callback=ret_value.append)
                r.wait()

                #输出结果
                file_part_value = ret_value[0]
                _result_password_ = file_part_value + added_password

            else:
                #小于等于20MB，直接在线程里计算
                file_part_value = calc_process(file_path)
                _result_password_ = file_part_value + added_password

            #限制记忆100个（实际好像是101个）文件历史结果数据；上“双保险”
            if (len(_file_result_record_) > 100) or (len(_file_path_record_) > 100):
                #如果超出，删掉最早的那个
                del _file_result_record_[0]
                del _file_path_record_[0]

            #添加一条记录
            _file_path_record_.append(file_path)
            _file_result_record_.append(file_part_value)


        else:
            #如果之前有记录，翻出记录，和密码拼接，输出
            _result_password_ = _file_result_record_[index_local] + added_password


    #文件路径框里有内容，但不存在
    elif file_path:
        _result_password_ = "【出错了，文件路径无效或者拖入了文件夹】" #向输出框发送出错信息

    #文件路径框里无内容，密码框里有内容
    elif added_password:
        _result_password_ = added_password #等于密码框里的内容

    else:
        _result_password_ = "" #都没有的话，输出空字符串

    #print(_result_password_)

    #传递任务结束信号，以重新启用按钮，并输出结果
    myWin.ms.task_stop.emit(True)

    return





#创建自定义信号
class MySignals(QObject):
    #task_start = pyqtSignal(bool)
    task_stop = pyqtSignal(bool)


class MyWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)
        self.action.clicked.connect(self.generate)#“生成”按钮
        self.clear_input.clicked.connect(self.clear_input_info)#“清除”按钮
        self.copy_to_clipboard.clicked.connect(self.copy_to_clp)#“复制”按钮
        self.clear_all_history.clicked.connect(self.clear_all_history_values)#“清除所有文件记忆”按钮
        self.clear_current_history.clicked.connect(self.clear_current_history_value)#“清除当前文件记忆”按钮

        self.file_drop_area.textChanged.connect(self.refresh_file_drop)

        #连接自定义信号
        self.ms = MySignals()
        #self.ms.task_start.connect(self.disable_button)
        self.ms.task_stop.connect(self.close_up)

        return

    def disable_button(self):
        self.action.blockSignals(True)#关“生成”按钮事件响应信号
        self.action.setEnabled(False)#暂时使“生成”按钮失效
        self.action.setText("处 理 中")

        self.clear_current_history.blockSignals(True)#关“清除当前文件记忆”按钮事件响应信号
        self.clear_current_history.setEnabled(False)#暂时使按钮失效
        return

    def close_up(self):
        self.output_area.setPlainText(_result_password_)#输出结果

        self.action.setText("生 成")
        self.action.setEnabled(True)#恢复“生成”按钮
        self.action.blockSignals(False)#开“生成”按钮事件响应信号
        
        #如果file_drop_area有东西，说明输入框刚刚接收到新的文件路径，
        #这里循环空指令等待refresh_file_drop(self)写入file_drop_display_layer
        if self.file_drop_area.toPlainText():
            for _ in range(10):
                pass

        #读取最新的文件输入框的内容，并检测是否在之前的记录内
        content = self.file_drop_display_layer.toPlainText()
        try:
            global _index_
            _index_ = _file_path_record_.index(content)
        except:
            pass
        else:
            #如果之前有记录，启用“清除当前文件记忆”按钮
            self.clear_current_history.setEnabled(True)#恢复按钮
            self.clear_current_history.blockSignals(False)#开按钮事件响应信号

        #设定处理状态为结束
        global _processing_
        _processing_ = False

        return



    def clear_input_info(self):#清空输入框内容，速度很快，不需要单独创建线程或者进程
        #查看文件路径保护复选框是否选中
        if not self.file_protect.isChecked():
            #文件路径被清空后，相当于文件路径改动了，这时同样需要关闭“清除当前文件记忆”按钮
            self.clear_current_history.blockSignals(True)#关“清除当前文件记忆”按钮事件响应信号
            self.clear_current_history.setEnabled(False)#暂时使按钮失效

            self.file_drop_display_layer.clear()

        #查看密码保护复选框是否选中
        if not self.password_protect.isChecked():
            self.password_input_area.clear()

        return

    def copy_to_clp(self):#复制结果至剪切板，速度很快，不需要单独创建线程或者进程
        wcb.OpenClipboard()
        wcb.EmptyClipboard()
        wcb.SetClipboardData(win32con.CF_UNICODETEXT, _result_password_)
        wcb.CloseClipboard()
        return

    def clear_all_history_values(self):#清除所有记忆的文件数据和对应的密码数据，速度很快，不需要单独创建线程或者进程
        #全部清掉之后，就没有记录可删了
        self.clear_current_history.blockSignals(True)#关“清除当前文件记忆”按钮事件响应信号
        self.clear_current_history.setEnabled(False)#暂时使按钮失效

        global _file_path_record_ , _file_result_record_
        _file_path_record_.clear()
        _file_result_record_.clear()

        return

    def clear_current_history_value(self):#清除当前文件的记忆数据，速度很快，不需要单独创建线程或者进程
        #按钮是“一次性”的，因为删除之后索引都会跟着变
        self.clear_current_history.blockSignals(True)#关“清除当前文件记忆”按钮事件响应信号
        self.clear_current_history.setEnabled(False)#暂时使按钮失效

        global _file_path_record_ , _file_result_record_ , _index_
        del _file_path_record_[_index_]
        del _file_result_record_[_index_]

        return


    def refresh_file_drop(self):#速度很快，不需要单独创建线程或者进程

        #暂时阻塞“file_drop_area”透明接收框的被修改信号，不然的话，文本改变了以后，又会触发事件，这样就
        #会一直不断循环嵌套调用“refresh_file_drop”，导致出不来，python报错
        self.file_drop_area.setReadOnly(True)#先设置只读，确保整个处理过程中没有新的文本写入
        self.file_drop_area.blockSignals(True)

        #一旦文件被改变，就需要重新验证是否在记录里，所以这时候要关掉“清除当前文件记忆”按钮
        self.clear_current_history.blockSignals(True)#关“清除当前文件记忆”按钮事件响应信号
        self.clear_current_history.setEnabled(False)#暂时使按钮失效
        
        #读取顶层透明接收区的文字，去掉开头的"file:///"
        content = self.file_drop_area.toPlainText().replace(r"file:///","",1)
        #设置下方显示层的文字为顶层透明接收区接收到的文字（显示给用户看的）
        self.file_drop_display_layer.setPlainText(content)
        #清空顶层透明接收区的文字
        self.file_drop_area.clear()

        #查看拖进来的文件是否有记录，如果有，就启用“清除当前文件记忆”按钮
        #不在运行中的拖放才能有用
        if not _processing_:
            global _index_
            try:
                _index_ = _file_path_record_.index(content)
            except:
                pass
            else:
                self.clear_current_history.setEnabled(True)#启用“清除当前文件记忆”按钮
                self.clear_current_history.blockSignals(False)#重新开启“清除当前文件记忆”按钮事件响应信号


        #恢复传送“file_drop_area”透明接收框的被修改信号
        self.file_drop_area.blockSignals(False)
        self.file_drop_area.setReadOnly(False)

        return


    #开始处理
    def generate(self):
        #传递任务开始信号，以暂时禁用按钮
        #self.ms.task_start.emit(True)
        self.disable_button()

        #发送运行中信号
        global _processing_
        _processing_ = True

        file_path=""
        file_path=self.file_drop_display_layer.toPlainText()#从输入框读取文件路径
        #file_path=file_path.replace(r"file:///","")#去掉开头的"file:///"

        added_password=""
        added_password=self.password_input_area.toPlainText()#从输入框读取密码
        added_password=added_password.replace("\n","")#去掉换行符以防万一

        #创建独立线程防止界面卡死
        t = threading.Thread(target=calc_thread,args=(file_path,added_password))
        t.start()

        return






if __name__ == '__main__':
    multiprocessing.freeze_support() # 在Windows下编译需要加这行
    app = QApplication(sys.argv)
 
    myWin = MyWindow()
    myWin.show()

    sys.exit(app.exec_())
