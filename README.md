
README
===========================
本插件使用Python编写，运行于Domoticz上，可以Domoticz中调节与AD8-DIN相连接的LED灯亮度, AD8-DIN需要通过一个RS485转TCP的网关接入到局域网，网关需要运行在TCP SERVER模式<br>
Current version: 0.1

介绍:
--------
AD8-DIN 是一款有 8 路输出的 LED 0-10V 调光器，该设备能输出 0-10V 至 LED 灯的调光电源，能通过RS485接收指令.<br>

USR-N520 是一款RS485转TCP的网关.<br>
AD8-DIN与USR-N520连接，USR-520通过网线连入局域网后，用户可以通过本插件控制已连接并设定好的 AD8-DIN<br>

本插件配合 AD8-DIN 和 USR-N520 使用(其他RS485转TCP的网关理论上也可，不过没测试过)<br>


Domoticz Plugin Options:
--------
##### IP Address:<br> 
RS485转TCP的网关的IP地址<br>
##### Port: <br>
RS485转TCP的网关的TCP SERVER 接收端口<br>
##### RS485 Addresses(Hex): <br>
AD8-DIN 在RS485总线上的地址，十六进制，以逗号、空格、或者|隔开，可以填写多个，例如 0x01, 0x02<br>


Product Links:
--------
AD8-DIN https://item.taobao.com/item.htm?id=554419257310_u=t2dmg8j26111<br>
USR-N520 https://detail.tmall.com/item.htm?spm=a230r.1.14.8.1ce053fbsIcRiU&id=531603030717&cm_id=140105335569ed55e27b&abbucket=3<br>


<br><br><br>
README
===========================
a Domoticz Python Plugin for one or more AD8-DIN 0-10V LED DIMMER which connects to a RS485-TCP router (USR-N520) running on the TCP SERVER mode.<br>
Current version: 0.1


Introduce:
--------
AD8-DIN is a LED Controller which can control 0-10V dimmable light by output 0-10V DC to LED STRIP, it can be controlled with RS485 commands.<br>
USR-N520 is a RS485-TCP router, with these two devices connected and set up, users can control LED Lights from Domoticz by this plugin.<br>
Designed for AD8-DIN and USR-N520 (Or other RS485 TO TCP Router, but not tested)<br>


Domoticz Plugin Options:
--------
##### IP Address:<br> 
IP address of TCP SERVER on RS485-TCP router<br>
##### Port: <br>
Port of TCP SERVER on RS485-TCP router<br>
##### RS485 Addresses(Hex): <br>
RS485 addresses of AD8-DIN, seperated by , or | or space, eg: 0x01, 0x02<br>


Product Links:
--------
AD8-DIN https://item.taobao.com/item.htm?id=554419257310_u=t2dmg8j26111<br>
USR-N520 https://detail.tmall.com/item.htm?spm=a230r.1.14.8.1ce053fbsIcRiU&id=531603030717&cm_id=140105335569ed55e27b&abbucket=3<br>

