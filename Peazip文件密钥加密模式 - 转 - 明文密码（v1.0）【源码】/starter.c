/*		encoding: GB 2312

Compiled On:                   VMware Workstation 15 Pro (15.5.6 build-16341506)
Client Operating System:       Windows 7 32bit [6.1.7601]
IDE:						DEV-C++ (5.11)

*/

#pragma comment(linker, "/subsystem:windows /entry:mainCRTStartup")
//编译不弹黑窗的选项

#include <windows.h>
#include <direct.h>

int main()
{
	_chdir("bin");//一定要先进入到文件夹（设定程序的工作文件夹）再启动exe，不然窗口左上角的图标显示不出来，还有可能会有其他意想不到的问题
	WinExec("main.exe",SW_SHOW);
	return 0;
}
