/*		encoding: GB 2312

Compiled On:                   VMware Workstation 15 Pro (15.5.6 build-16341506)
Client Operating System:       Windows 7 32bit [6.1.7601]
IDE:						DEV-C++ (5.11)

*/

#pragma comment(linker, "/subsystem:windows /entry:mainCRTStartup")
//���벻���ڴ���ѡ��

#include <windows.h>
#include <direct.h>

int main()
{
	_chdir("bin");//һ��Ҫ�Ƚ��뵽�ļ��У��趨����Ĺ����ļ��У�������exe����Ȼ�������Ͻǵ�ͼ����ʾ�����������п��ܻ����������벻��������
	WinExec("main.exe",SW_SHOW);
	return 0;
}
