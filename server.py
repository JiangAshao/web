# -*- coding:utf-8 
_author_='lhw'
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys,io,os
import subprocess
# subprocess 进程类
class ServerException(Exception):
	#服务器内部错误
	pass
class base_case(object):
	def handle_file(self,handler,full_path):
		try:
			with open(full_path,'rb') as f:
				content=f.read()
			handler.send_content(content)
		except Exception as msg:
			print(msg)
			msg='{0} cannot be read:{1}'.format(full_path,msg)
			handler.handle_error(msg)
	#浏览器访问根url的时候能返回工作目录下index.html的内容
	def index_path(self,handler):
		return os.path.join(handler.full_path,'index.html')
	#要求子类必须实现的接口
	def test(self,handler):
		assert False, 'Not implemented.'
	def act(self,handler):
		#断言 用来定义抽象函数
		assert False, 'Not implemented.'
class case_no_file(base_case):
	#文件不存在，返回True
	def test(self,handler):
		return not os.path.exists(handler.full_path)
	def act(self,handler):
		#抛出异常，文件未找到
		raise ServerException('{0} not found'.format(handler.path))
class case_existing_file(base_case):
	#文件存在
	def test(self,handler):
		return os.path.isfile(handler.full_path)
	def act(self,handler):
		#处理该文件
		self.handle_file(handler,handler.full_path)
class case_always_fail(base_case):
	#所有情况都不符合时的默认处理类
	def test(self,handler):
		return True
	def act(self,handler):
		raise ServerException('Unknown Object {0}'.format(handler.path))
class case_directory_index_file(base_case):
	#判断目标路径是否是目录 & 目录下是否有index.html
	def test(self,handler):
		return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))
	def act(self,handler):
		#响应index.html
		self.handle_file(handler,self.index_path(handler))
class case_cgi_file(base_case):
	#处理脚本文件
	def run_cgi(self,handler):
		data=subprocess.check_output(["python", handler.full_path])
		#父进程等待子进程完成返回子进程向标准输出的输出结果
		handler.send_content(data)
	def test(self,handler):
		return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')
	def act(self,handler):
		#运行脚本文件
		self.run_cgi(handler)
class RequestHandler(BaseHTTPRequestHandler):
	#请求路径合法则返回相应处理
	#否则返回错误页面
	# 所有可能的情况
	Cases = [case_no_file,
			case_cgi_file,
			case_existing_file,
			case_directory_index_file,
			case_always_fail]
	#处理请求并返回页面
	Error_Page = '''\
		<html>
			<body>
				<h1>Error accessing {path}</h1>
				<p>{msg}</p>
			</body>
		</html>
	'''	
	
	def send_content(self,page,status=200):
		self.send_response(status)
		self.send_header("Content-Type", "text/html")
		#需要将Page编码成bytes,否则报错
		#bytes解码会得到str str编码会变成bytes
		self.send_header("Content-Length", str(len(page)))
		#发送一个空白行，表明HTTP头响应结束
		self.end_headers()
		#以二进制进行读出的内容就是bytes，不用进行编码
		#判断page的类型，如果是str,需要进行编码
		if isinstance(page,str):
			page=page.encode('ascii')
		self.wfile.write(page)
	
	def handle_error(self,msg):
		content=self.Error_Page.format(path=self.path,msg=msg)
		self.send_content(content,404)
	#处理一个get请求  重写的一个方法
	def do_GET(self):
		try:
			#文件的完整路径			
			self.full_path=os.path.join(os.getcwd(),self.path.replace('/',''))
			#遍历所有可能的情况
			for case in self.Cases:
				#实例化
				handler=case()
				#是否符合情况
				if handler.test(self):
					#符合情况，进行相应处理
					handler.act(self)
					break			
		#处理异常
		except Exception as msg:
			self.handle_error(msg)
		
if __name__=='__main__':
	serverAddress=('',8080)
	server=HTTPServer(serverAddress,RequestHandler)
	print('Server started on 127.0.0.1,port 8080.....')
	server.serve_forever()