# -*- coding: utf-8 -*-
# AD8-DIN
#
# Author: itpansic
#

"""
<plugin key="AD8-DIN" name="AD8-DIN" author="itpansic" version="1.0.0" wikilink="https://github.com/itpansic/AD8-DIN" externallink="https://item.taobao.com/item.htm?id=554419257310&_u=t2dmg8j26111">
    <description>
        <h2>AD8-DIN 0-10V LED DIMMER</h2><br/>
        Plugin for one or more AD8-DIN 0-10V LED DIMMER which connects to a RS485-TCP router (Model Name:USR-N520) running on the TCP SERVER mode.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Designed for AD8-DIN and USR-N520</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Dimmer - control brightness of one light.</li>
        </ul>
        <h3>Configuration</h3>
            <li>IP Address:         IP address of TCP SERVER on RS485-TCP router</li>
            <li>Port:               Port of TCP SERVER on RS485-TCP router</li>
            <li>RS485 Addresses(Hex): RS485 addresses of AD8-DIN, seperated by , or | or space</li>

    </description>
    <params>
        <param field="Address" label="IP Address" width="200px"/>
        <param field="Port" label="Port" width="50px" required="true" default="23"/>
        <param field="Mode1" label="RS485 Addresses(Hex)" width="180px" required="true" default="0x01"/>
        <param field="Mode2" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import queue
import threading
import time
import re
import Domoticz

# 查询的最少间隔时间
minRefreshDuration = 9

# LED控制器类，每个对象对应一个AD8-DIN
class LedCtrl:
    # 是否连通
    online = False
    # 其管理的开关
    dicDevice = None
    # 其管理的渐变时间
    dicDeviceGradientDuration = None
    # RS485地址码
    address = None

    # 上个发送的命令是否是查询渐变时间
    isLastNeedWaitCmdGetGradientDuration = False

    def __init__(self, address):

        self.address = address
        self.dicDevice = {}
        self.dicDeviceGradientDuration = {}

    # 查询本设备所有亮度信息，以及查询渐变时间
    def onQueryLight(self):
        arrayCmd = []
        # 查询亮度
        for device in self.dicDevice.values():
            dicOptions = device.Options
            if dicOptions and 'LJLightIndex' in dicOptions and int(dicOptions['LJLightIndex']) > 0:
                # 加入到命令列表
                arrayCmd.append(self.cmdGetBrightness(int(dicOptions['LJLightIndex'])))
        return arrayCmd

    # 查询本设备渐变时间
    def onQueryGradientDuration(self):
        return self.cmdGetGradientDuration()

    def cmdGetBrightness(self, lightIndex):
        #AE01A8F2EE 查询0x01的第8路亮度
        return 'AE{0:0>2}A{1}F2EE'.format(self.address,int(lightIndex))

    def cmdGetGradientDuration(self):
        #AE01C100EE 查询渐变时间
        return 'AE{0:0>2}C100EE'.format(self.address)

    def cmdSetGradientDuration(self, gradientDuration):
        #AE01C206EE 设置渐变时间为6秒
        if gradientDuration < 1: gradientDuration = 1
        if gradientDuration > 15: gradientDuration = 15
        hexText = str(hex(gradientDuration))[2:]
        return 'AE{0:0>2}C2{1:0>2}EE'.format(self.address, hexText)

    def cmdSetBrightness(self, lightIndex, brightness):
        #AE01B864EE 设置0x01的第8路亮度渐变到100
        #AE010864EE 设置0x01的第8路亮度到100
        hexText = str(hex(brightness))[2:].upper()
        if len(self.dicDeviceGradientDuration)>0 and list(self.dicDeviceGradientDuration.values())[0].nValue == 0:
            # 未开启渐变
            cmd = 'AE{0:0>2}0{1}{2:0>2}EE'.format(self.address, lightIndex, hexText)
        else:
            # 开启了渐变
            cmd = 'AE{0:0>2}B{1}{2:0>2}EE'.format(self.address, lightIndex, hexText)
        Domoticz.Log('cmdSetBrightness ' + cmd)
        return cmd

    # 打开指定Unit的灯
    def onSetOn(self, unit, brightness):
        if brightness > 100: brightness = 100
        if brightness < 0: brightness = 0
        device = Devices[unit]
        if device:
            lightIndex = int(device.Options['LJLightIndex'])
            if not self.conn.Connected():
                # 未连接，恢复调整之前的数据
                UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)
            elif lightIndex in range(1, 9):
                UpdateDevice(Unit=unit, nValue=1, sValue=str(brightness))
                return self.cmdSetBrightness(lightIndex, int(brightness))
        return None

    # 关闭指定Unit的灯
    def onSetOff(self, unit, brightness):
        if brightness > 100: brightness = 100
        if brightness < 0: brightness = 0
        device = Devices[unit]
        if device:
            lightIndex = int(device.Options['LJLightIndex'])
            if not self.conn.Connected():
                # 未连接，恢复调整之前的数据
                UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)
            elif lightIndex in range(1, 9):
                UpdateDevice(Unit=unit, nValue=0, sValue=device.sValue)
                return self.cmdSetBrightness(lightIndex, 0)
        return None

    def onSetBrightness(self, unit, brightness):
        if brightness > 100: brightness = 100
        if brightness < 0: brightness = 0
        device = Devices[unit]
        if device:
            lightIndex = int(device.Options['LJLightIndex'])
            if not self.conn.Connected():
                # 未连接，恢复调整之前的数据
                UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)
            elif lightIndex in range(1, 9):
                UpdateDevice(Unit=unit, nValue=0 if int(brightness == 0) else 1, sValue=str(brightness))
                return self.cmdSetBrightness(lightIndex, int(brightness))
        return None

    def onSetGradientDuration(self, unit, gradientDuration):
        if gradientDuration > 15: gradientDuration = 15
        if gradientDuration < 1: brightness = 1
        device = self.dicDeviceGradientDuration[unit]
        if device:
            lightIndex = int(device.Options['LJLightIndex'])
            if not self.conn.Connected():
                # 未连接，恢复调整之前的数据
                UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)
            elif lightIndex == 0:
                Domoticz.Log('cmdSetGradientDuration: {0}'.format(self.cmdSetGradientDuration(int(gradientDuration))))
                UpdateDevice(Unit=unit, nValue=1, sValue=int(gradientDuration)*10)
                return self.cmdSetGradientDuration(int(gradientDuration))
        return None


    def handleCmdReceived(self, dicCmd):
        recv = dicCmd['cmd']

        if self.isLastNeedWaitCmdGetGradientDuration and len(recv) == 2 and int(recv, 16) >= 1 and int(recv, 16) <= 15:
            # 是发给本对象的渐变时间查询反馈指令
            #更新数据
            for unit, device in self.dicDeviceGradientDuration.items():
                if self.shouldDeviceUpdate(device):
                    UpdateDevice(Unit=unit, nValue=device.nValue, sValue=int(recv, 16)*10)
                break

        elif recv and recv[2:4] == self.address:
            # 是发给本对象的亮度查询反馈消息，解析出灯号和亮度值
            if not self.online:
                self.online = True
                Domoticz.Log('Led Ctrl 0x{} online now!'.format(self.address))
            lightIndex = recv[5:6]
            brightness = int(recv[6:8], 16)

            if brightness > 100: brightness = 100

            nValue = 1 if brightness > 0 else 0
            sValue = str(brightness)

            #更新数据
            for unit, device in self.dicDevice.items():
                if device.Options['LJLightIndex'] == lightIndex and self.shouldDeviceUpdate(device):
                    UpdateDevice(Unit=unit, nValue=nValue, sValue=sValue)
                    break

    # 是否应该更新设备
    def shouldDeviceUpdate(self, device):
        if not device: return False
        if device.TimedOut == 0 and device.Options['LJLightIndex'] == '0' and device.nValue == 0:
            # 如果开关是在线并且不渐变状态，则不更新渐变时长到开关
            return False

        timeLast = time.mktime(time.strptime(device.LastUpdate,"%Y-%m-%d %H:%M:%S"))

        if device.TimedOut > 0 or (timeLast and time.time() - timeLast) > 7:
            # 离线后首次收到消息，或者7秒之前更新过，才把数据更新到系统
            return True
        else:
            Domoticz.Log('Pass update because updated in last 7 sec :' + descDevice(device))
            return False

    # 检查收到数据合法性
    def checkRecvData(self, recv):
        recv = recv.upper()
        return len(recv) >= 10 and recv[0:2] == 'AE'and recv[8:10] == 'EE' and recv[4:5] == 'D'

    # 更新开关状态为未在线
    def offline(self):
        if self.online:
            self.online = False
            Domoticz.Log('Led Ctrl 0x{} offline now!'.format(self.address))

        for unit, device in self.dicDevice.items():
            UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)
        for unit, device in self.dicDeviceGradientDuration.items():
            UpdateDevice(Unit=unit, nValue=device.nValue, sValue=device.sValue, TimedOut=1)


class Ad8din:
    # 自上次读取一次新信息起经过了多久
    lastRefreshTimestamp = time.time()

    messageQueue = None
    messageThread = None

    conn = None
    # 待发送的需要等待回复的命令，成员格式为:{"address":"XX", "cmd":"XXXXXXX", "type": "brightness", "timestamp": timestamp}
    arrayCmdNeedWait = []
    # 待发送的不需等待回复的命令，成员格式为:{"address":"XX", "cmd":"XXXXXXX", "type": "gradientDuration", "timestamp": timestamp}
    arrayCmd = []
    # 正在等待回应的命令
    dicCmdWaiting = None

    # 存储各个AD8-DIN控制器的dic, key:字符串表示的控制器16位地址 value:LedCtrl对象
    dicLedCtrl = {}

    # 收到但仍未处理的数据字符串
    recv = ''

    def __init__(self):
        self.messageQueue = queue.Queue()
        self.messageThread = threading.Thread(name="QueenSendThread", target=Ad8din.handleSend,
                                              args=(self,))
        self.recv = ''
        return

    def onStart(self):

        self.messageThread.start()

        # 取得设置的AD8-DIN的RS485地址列表
        if Parameters["Mode2"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)

        self.conn = Domoticz.Connection(Name="AD8-DIN", Transport="TCP/IP", Protocol="line",
                                        Address=Parameters['Address'],
                                        Port=Parameters["Port"])
        self.conn.Connect()

        # 从Domoticz重新加载硬件和设备信息
        self.reloadFromDomoticz()

        # 先把所有设备重置为未连接
        for ledCtrl in self.dicLedCtrl.values():
            ledCtrl.offline()


    def onStop(self):
        Domoticz.Log("onStop called")
        # signal queue thread to exit
        self.messageQueue.put(None)
        Domoticz.Log("Clearing message queue...")
        self.messageQueue.join()

        # Wait until queue thread has exited
        Domoticz.Log("Threads still active: "+str(threading.active_count())+", should be 1.")
        while (threading.active_count() > 1):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name):
                    Domoticz.Log("'"+thread.name+"' is still running, waiting otherwise Domoticz will abort on plugin exit.")
            time.sleep(1.0)
        return

    def onConnect(self, Connection, Status, Description):
        if Status == 0:
            Domoticz.Log("Connect Success!")
            # 查询各设备在线状态
            self.checkLedCtrlOnline()

        else:
            Domoticz.Log("Connect Failed:" + Description)
            for ledCtrl in self.dicLedCtrl.values():
                ledCtrl.offline()


    def onMessage(self, Connection, Data):
        if Connection.Name != 'AD8-DIN': return

        recv = Data.hex().upper()

        Domoticz.Debug('TCP/IP MESSAGE RECEIVED ' + recv)

        # 截取合法命令
        i = 16
        dicCmd = self.getCmdClip(recv)

        self.procDicCmd(dicCmd)

        dicCmd = self.getCmdClip()
        while i > 0 and dicCmd:
            self.procDicCmd(dicCmd)
            dicCmd = self.getCmdClip()
            i -= 1


    def handleSend(self):
        try:
            Domoticz.Debug("Entering handleSend")
            while True:
                Message = self.messageQueue.get(block=True)
                if Message is None:
                    Domoticz.Debug("Exiting handleSend")
                    self.messageQueue.task_done()
                    break

                if (Message["Type"] == "Send"):

                    if (Message["Bytes"]):
                        if not self.conn.Connected():
                            Domoticz.Log('Not connected. Now connecting...')
                            self.conn.Connect()
                        else:
                            time.sleep(0.1)
                            self.conn.Send(Message=Message["Bytes"])
                    else:
                        Domoticz.Log("Send quest have no Bytes")

                self.messageQueue.task_done()
        except Exception as err:
            Domoticz.Error("handleSend: "+str(err))


    # 处理收到的命令
    def procDicCmd(self, dicCmd):
        Domoticz.Debug('procDicCmd:   ' + str(dicCmd))
        if not dicCmd: return
        cmdWaiting = None
        cmdTypeWaiting = None
        addressWaiting = None
        ledCtrlWaiting = None

        cmd = None
        cmdType = None
        address = None
        ledCtrl = None
        if dicCmd and 'type' in dicCmd and 'cmd' in dicCmd:
            cmd = dicCmd['cmd']
            cmdType = dicCmd['type']
            if cmd and len(cmd) >= 4 and cmdType and cmdType == 'brightness':
                address = cmd[2:4]
                if address and address in self.dicLedCtrl:
                    ledCtrl = self.dicLedCtrl[address]
        else:
            return

        if self.dicCmdWaiting and 'type' in self.dicCmdWaiting and 'cmd' in dicCmd:
            cmdTypeWaiting = self.dicCmdWaiting['type']
            cmdWaiting = self.dicCmdWaiting['cmd']
            if cmdWaiting and len(cmdWaiting) >= 4:
                addressWaiting = cmdWaiting[2:4]
                if addressWaiting and addressWaiting in self.dicLedCtrl:
                    ledCtrlWaiting = self.dicLedCtrl[addressWaiting]

        if ledCtrl and not ledCtrl.online:
            # 该地址对应的控制器处于下线状态，改为在线状态并发送查询各路亮度命令
            ledCtrl.online = True
            Domoticz.Log('Led Ctrl 0x{} online now!'.format(ledCtrl.address))


            array = ledCtrl.onQueryLight()
            for cmd in array:
                self.goingToSendCmd(address=address, cmd=cmd, type='brightness', needWaiting=True)

            # 查询渐变时间会导致暗的灯闪烁
            cmdDuration = ledCtrl.onQueryGradientDuration()
            self.goingToSendCmd(address=address, cmd=cmdDuration, type='gradientDuration', needWaiting=True)

        if cmd and cmdType and cmdWaiting and cmdTypeWaiting and addressWaiting and cmdType == cmdTypeWaiting:
            # 收到的命令正是正在等待的
            if cmdType == 'brightness' and address and addressWaiting and address == addressWaiting:
                # 亮度返回
                if ledCtrl:
                    ledCtrl.handleCmdReceived(dicCmd)
                self.dicCmdWaiting = None
                self.sendNextCmd()

            elif cmdType == 'gradientDuration' and ledCtrlWaiting:
                # 渐变时间返回
                ledCtrlWaiting.handleCmdReceived(dicCmd)
                self.dicCmdWaiting = None
                self.sendNextCmd()


    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        params = params.capitalize()
        device = Devices[Unit]
        if device.Options['LJAddress'] not in self.dicLedCtrl:
            return
        ledCtrl = self.dicLedCtrl[device.Options['LJAddress']]
        if not ledCtrl.online: return
        Domoticz.Log('action: {0} sep: {1} params: {2} Level: {3}'.format(action, sep, params, Level))

        cmd = None
        if action == 'On':
            if device.Options['LJLightIndex'] == '0':
                # 渐变时间调节
                if Level > 150: Level = 150
                if Level <= 1:
                    # 关闭渐变
                    UpdateDevice(Unit=Unit, nValue=0, sValue='0')
                else:
                    cmd = ledCtrl.onSetGradientDuration(Unit, int(int(Level) / 10))
                    self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='gradientDuration',needWaiting=False)
            else:
                cmd = ledCtrl.onSetOn(Unit, Level)
                if cmd:
                    self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='brightness',needWaiting=False)
        elif action == 'Off':
            if device.Options['LJLightIndex'] == '0':
                # 渐变时间调节
                UpdateDevice(Unit=Unit, nValue=0, sValue='0')
            else:
                cmd = ledCtrl.onSetOff(Unit, Level)
                if cmd:
                    self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='brightness',needWaiting=False)
        elif action == 'Set' and params == 'Level':
            if device.Options['LJLightIndex'] == '0':
                # 渐变时间调节
                if Level > 150: Level = 150
                if Level <= 1:
                    # 关闭渐变
                    UpdateDevice(Unit=Unit, nValue=0, sValue='0')
                else:
                    cmd = ledCtrl.onSetGradientDuration(Unit, int(int(Level) / 10))
                    if cmd:
                        self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='gradientDuration',needWaiting=False)
            else:
                cmd = ledCtrl.onSetBrightness(Unit, Level)
                if cmd:
                    self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='brightness',needWaiting=False)


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
        for ledCtrl in self.dicLedCtrl.values():
            ledCtrl.offline()
        self.conn.Connect()

    def onHeartbeat(self):
        Domoticz.Debug('onHeartbeat Called ---------------------------------------')
        # 如果没连接则尝试重新连接
        if not self.conn.Connected():
            Domoticz.Log('Not connected. Now connecting...')
            self.conn.Connect()

        # 清除超过20秒未发的需要等待回复的命令，并将对应控制器设置为不在线
        nowTime = int(time.time())
        arrayTmp = []
        for cmdObject in self.arrayCmdNeedWait:
            if nowTime - cmdObject['timestamp'] > 20:
                arrayTmp.append(cmdObject)

        for cmdDel in arrayTmp:
            self.arrayCmdNeedWait.remove(cmdDel)


        # 检查命令接收情况
        if self.dicCmdWaiting and 'timestamp' in self.dicCmdWaiting:
            timestamp = self.dicCmdWaiting['timestamp']
            if nowTime - timestamp > 2:
                Domoticz.Log('WARNING: Cmd waiting time out, clean. ' + str(self.dicCmdWaiting))
                #超过2秒仍没收到消息，则代表设备不在线，清理所有未发送的命令

                if 'address' in self.dicCmdWaiting and self.dicCmdWaiting['address'] in self.dicLedCtrl:
                    ledCtrl = self.dicLedCtrl[self.dicCmdWaiting['address']]
                    ledCtrl.offline()

                    arrayTmp = []
                    for cmdObject in self.arrayCmdNeedWait:
                        if 'address' in cmdObject and cmdObject['address'] == str(ledCtrl.address):
                            arrayTmp.append(cmdObject)
                    for cmdDel in arrayTmp:
                        Domoticz.Log('Delete cmd: ' + str(cmdDel))
                        self.arrayCmdNeedWait.remove(cmdDel)
                self.dicCmdWaiting = None
                self.sendNextCmd()




         # 最快每minRefreshDuration秒查询一次
        global minRefreshDuration
        if not self.conn.Connected() or time.time() - self.lastRefreshTimestamp < minRefreshDuration:
            return
        self.lastRefreshTimestamp = nowTime
        Domoticz.Debug('Query Light Status...')
        # 查询灯具状态
        for ledCtrl in self.dicLedCtrl.values():

            array = ledCtrl.onQueryLight()
            # 查询渐变时间会导致暗的灯闪烁，取消每次都查询
            # cmdDuration = ledCtrl.onQueryGradientDuration()
            # if cmdDuration:
            #    self.goingToSendCmd(address=ledCtrl.address, cmd=cmdDuration, type='gradientDuration', needWaiting=True)

            for cmd in array:
                self.goingToSendCmd(address=ledCtrl.address, cmd=cmd, type='brightness', needWaiting=True)


        # 检测在线情况
        self.checkLedCtrlOnline()

    # 截取一段收到的数据中的合法指令
    def getCmdClip(self, recv=None):
        if recv:
            self.recv += recv.upper()
        recvLen = len(self.recv)
        if recvLen > 200:
            self.recv = self.recv[-200:]

        patternBrightness = re.compile(r'AE[0-F][0-F]D[1-8][0-F][0-F]EE')   # re.I 表示忽略大小写
        mBrightness = patternBrightness.search(self.recv)
        dicCmd = None
        if mBrightness:
            # 和之前的缓存组成了合法亮度反馈指令
            self.recv = self.recv[mBrightness.end():]
            dicCmd = {'cmd':mBrightness.group(), 'type':'brightness'}

        elif recv and len(recv) == 2 and int(recv, 16) >= 1 and int(recv, 16) <= 255:
            # 与之前的缓存无法组成合法亮度反馈指令，但是收到的数据符合渐变时间反馈特征
            self.recv = ''
            dicCmd = {'cmd':recv.upper(), 'type':'gradientDuration'}

        if dicCmd:
            Domoticz.Debug('RECEIVED CMD: ' + str(dicCmd))
        return dicCmd

    # 发送命令检测控制器是否在线
    def checkLedCtrlOnline(self):
        #AE01A1F2EE 查询0x01的第1路亮度
        #AE02A1F2EE 查询0x01的第1路亮度
        aSet = self.setAddress()
        for address in aSet:
            cmd = 'AE{0:0>2}A1F2EE'.format(address)
            if self.dicLedCtrl:
                ledCtrl = self.dicLedCtrl[address]
                if ledCtrl and ledCtrl.online:
                    continue

            a_bytes = bytearray.fromhex(cmd)
            self.messageQueue.put({"Type": "Send", "Bytes": a_bytes})
            Domoticz.Debug('TCP/IP MESSAGE SEND ' + cmd)


    def setAddress(self):
        strListLedCtrl = Parameters["Mode1"]
        strListLedCtrl = strListLedCtrl.replace(',', '')
        strListLedCtrl = strListLedCtrl.replace('|', '')
        strListLedCtrl = strListLedCtrl.replace(' ', '')
        strListLedCtrl = strListLedCtrl.replace('0X', '0x')
        strListLedCtrl = strListLedCtrl.replace('X', '0x')
        setAddressTmp = set(strListLedCtrl.split('0x'))
        setAddress = set([])
        for tmp in setAddressTmp:
            if not tmp or len(tmp) < 1:
                continue
            setAddress.add(tmp.upper())

        return setAddress

    def reloadFromDomoticz(self):
        self.dicLedCtrl = {}
        aSet = self.setAddress()
        for tmp in aSet:
            self.dicLedCtrl[tmp] = LedCtrl(tmp)
            self.dicLedCtrl[tmp].conn = self.conn

        # 记录已有的unit
        setUnit = set([])
        # 待删除的device对应的unit
        setUnitDel = set([])
        # 所有的Unit集合
        setUnitAll = set(range(1, 256))
        # 将Device放入对应的控制器对象中，多余的device删除
        for unit in Devices:
            device = Devices[unit]
            dicOptions = device.Options
            Domoticz.Log("DEVICE FROM PANEL " + descDevice(device=device, unit=unit))
            if dicOptions and 'LJAddress' in dicOptions and 'LJLightIndex' in dicOptions and dicOptions['LJAddress'] in self.dicLedCtrl:
                # 有匹配的控制器，赋值
                if dicOptions['LJLightIndex'] == '0':
                    # 渐变查询
                    if len(self.dicLedCtrl[dicOptions['LJAddress']].dicDeviceGradientDuration) > 0:
                        #已经有现成的渐变时长设备，加入待删除
                        Domoticz.Log('Already have gradient duration device, add to delete list. ' + device.Name)
                        setUnitDel.add(unit)
                    else:
                        self.dicLedCtrl[dicOptions['LJAddress']].dicDeviceGradientDuration[unit] = device
                else:
                    # 调光开关
                    if unit in self.dicLedCtrl[dicOptions['LJAddress']].dicDevice:
                        #已经有对应Unit的调光开关，加入待删除
                        Domoticz.Log('Already have unit device, add to delete list. ' + device.Name)
                        setUnitDel.add(unit)
                    else:
                        self.dicLedCtrl[dicOptions['LJAddress']].dicDevice[unit] = device
                setUnit.add(unit)
            else:
                # 没匹配的控制器，加入待删除
                setUnitDel.add(unit)
        Domoticz.Log("DELETE DEVICES IN UNIT: " + str(setUnitDel))

        # 删除多余的Device
        for unit in setUnitDel:
            Devices[unit].Delete()

        # 遍历控制器，补全控制器对应的device
        for address in self.dicLedCtrl:
            # 当前控制器的设备字典
            dicDevice = self.dicLedCtrl[address].dicDevice
            dicDeviceGradientDuration = self.dicLedCtrl[address].dicDeviceGradientDuration
            # 用来统计设置中已存在的调光序号
            setLightIndexExist = set([])
            for device in dicDevice.values():
                setLightIndexExist.add(int(device.Options['LJLightIndex']))
            for device in dicDeviceGradientDuration.values():
                setLightIndexExist.add(int(device.Options['LJLightIndex']))
            Domoticz.Log("LED CONTROLLER 0x" + address + " NOW HAVE DEVICES IN LIGHT INDEXES: " + str(setLightIndexExist))
            setAll = set(range(0, 9))
            # 缺失待添加的设备调光序号
            setAll.difference_update(setLightIndexExist)
            Domoticz.Log("FILL UP WITH LIGHT INDEXES: " + str(setAll))
            levelNames = '不渐变|1档|2档|3档|4档|5档|6档|7档|8档|9档|10档|11档|12档|13档|14档|15档'
            optionsGradient = {'LevelActions': '|' * levelNames.count('|'),
                                'LevelNames': levelNames,
                                'LevelOffHidden': 'true',
                                'SelectorStyle': '1'}
            # Check if images are in database
            if "LJCountDown" not in Images:
                Domoticz.Image("LJCountDown.zip").Create()
            image = Images["LJCountDown"].ID
            for lightIndex in setAll:
                # 为每个待添加的设备序列号添加设备
                # 首先分配unit
                setAvariable = setUnitAll.difference(setUnit)
                if not setAvariable or len(setAvariable) == 0:
                    continue
                minUnit = min(setAvariable)
                setUnit.add(minUnit)
                optionsCustom = {'LJAddress' : address, 'LJLightIndex' : str(lightIndex)}

                # 添加设备
                if lightIndex == 0:
                    # 渐变时间
                    name = '控制器 0x{} 渐变时间'.format(address)

                    dicDeviceGradientDuration[minUnit] = Domoticz.Device(Name=name, Unit=minUnit, TypeName="Selector Switch", Switchtype=18, Image=image, Options=dict(optionsCustom, **optionsGradient))
                    dicDeviceGradientDuration[minUnit].Create()
                    Domoticz.Log('ADD DEVICE GRADIENT DURATION DIMMER:'+ descDevice(device=dicDeviceGradientDuration[minUnit], unit=minUnit))
                else:
                    # 调光开关
                    name = '控制器 0x{} 开关{}'.format(address, lightIndex)
                    dicDevice[minUnit] = Domoticz.Device(Name=name, Unit=minUnit, Type=244,Subtype=73, Switchtype=7, Options=optionsCustom)
                    dicDevice[minUnit].Create()
                    Domoticz.Log('ADD DEVICE BRIGHTNESS DIMMER:'+ descDevice(device=dicDevice[minUnit], unit=minUnit))

    # 添加命令到待发送列表
    def goingToSendCmd(self, address, cmd, type, needWaiting = False):
        if not cmd or len(cmd) < 1 or str(address) not in self.dicLedCtrl:
            return
        if not self.conn.Connected():
            Domoticz.Log('Not Connected, cmd {} ignored.'.format(cmd))
            return

        if not self.dicLedCtrl[str(address)].online:
            Domoticz.Log('Device Offline, cmd {} ignored.'.format(cmd))
            return
        array = self.arrayCmdNeedWait if needWaiting else self.arrayCmd
        # 太多命令未发送，则忽略新命令
        if len(array) > len(self.dicLedCtrl) * 20:
            Domoticz.Log('WARNING: Too many cmd waitting to send, ignore new cmd!!!')
            return

        cmdObject = {'address':str(address), 'cmd' : cmd, 'type' : type, 'timestamp' : int(time.time())}
        array.append(cmdObject)
        self.sendNextCmd()

    # 发送命令
    def sendNextCmd(self):
        if self.dicCmdWaiting or not self.conn or not self.conn.Connected():
            return
        array = None
        needWait = None
        if len(self.arrayCmd) > 0:
            # 优先发送不用等待的命令
            array = self.arrayCmd
            needWait = False
        elif len(self.arrayCmdNeedWait) > 0:
            array = self.arrayCmdNeedWait
            needWait = True
        else:
            return

        cmdObject = array.pop(0)
        cmd = cmdObject['cmd']
        a_bytes = bytearray.fromhex(cmd)

        # 判断是不是查询渐变时间命令
        pattern = re.compile(r'AE[0-F][0-F]C100EE')   # re.I 表示忽略大小写
        m = pattern.search(cmd)
        if m and needWait:
            address = m.group()[2:4]
            if address in self.dicLedCtrl:
                ledCtrl = self.dicLedCtrl[address]
                ledCtrl.isLastNeedWaitCmdGetGradientDuration = True
            else:
                ledCtrl.isLastNeedWaitCmdGetGradientDuration = False
        Domoticz.Debug('TCP/IP MESSAGE SEND ' + cmd)
        self.messageQueue.put({"Type": "Send", "Bytes": a_bytes})

        if needWait:
            self.dicCmdWaiting = cmdObject
        else:
            self.sendNextCmd()


global _pluginAd8din
_pluginAd8din = Ad8din()

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, updateAnyway=True):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if updateAnyway or (Devices[Unit].nValue != nValue) or (sValue >= 0 and Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug("UPDATE DEVICE "+ descDevice(Devices[Unit], unit=Unit, nValue=nValue, sValue=sValue))
    return

def logConnectStatus(conn):
    if conn:
        Domoticz.Log('~~~~~~~~~~~Connecting: ' + str(conn.Connecting()) + ' Connected: ' + str(conn.Connected()))

def descDevice(device, unit=None, nValue = None, sValue = None):
    if not device: return''
    n = nValue if nValue else device.nValue
    s = sValue if sValue else device.sValue
    address = 'XX' if 'LJAddress' not in device.Options else device.Options['LJAddress']
    lightIndex = 'XX' if 'LJLightIndex' not in device.Options else device.Options['LJLightIndex']
    return 'Unit: {}, Name: {}, nValue: {}, sValue: {}, TimedOut: {} Ctrl: 0x{:0>2}, LightIndex: {}'.format(unit, device.Name, n, s, device.TimedOut, address, lightIndex,)

def onStart():
    global _pluginAd8din
    _pluginAd8din.onStart()

def onStop():
    global _pluginAd8din
    _pluginAd8din.onStop()

def onConnect(Connection, Status, Description):
    global _pluginAd8din
    _pluginAd8din.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _pluginAd8din
    _pluginAd8din.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _pluginAd8din
    _pluginAd8din.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _pluginAd8din
    _pluginAd8din.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _pluginAd8din
    _pluginAd8din.onDisconnect(Connection)

def onHeartbeat():
    global _pluginAd8din
    _pluginAd8din.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
