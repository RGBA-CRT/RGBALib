# ----------------------------------------------------------
# ActiveBasic to C Transformation helper v0.0
#                        PROGRAMMED BY RGBA_CRT 2018-10
# ----------------------------------------------------------

message="/*----------------------------------------------------------\n * ActiveBasic to C Transformation helper v0.0\n *                       PROGRAMMED BY RGBA_CRT 2018-10\n *----------------------------------------------------------*/\n"

import sys
import re
def remove_head_space(str):
	i=0
	while(1):
		if len(str)<=i: break
		if str[i]==' ': 
			i+=1
			continue
		break
		
	return str[i:]
	
def isSpaceChar(ch):
	
	if ((ch.find(' ') > -1) or (ch.find(',') > -1) or (ch.find("\t") > -1)):
		return True
	else:
		return False

def isSplitChar(ch):
	splitChar=['(',')','\'']
	if (ch in splitChar):
		return True
	else:
		return False

def ab_split(str):
	
	ignore_pair={
		'"' : '"',
		"'" : '\n'
	}
	ret_list = []
	start=0
	cur=0
	
	while(1):
		if len(str)<=cur: break

		# かっこの中身は無視
		if str[cur] in ignore_pair:
			ignore_key=str[cur]
			if ignore_key=="'":
				cur+=1

			if cur!=start:
				ret_list.append(str[start:cur])	
			start=cur
			cur+=1
			while(1):
				if len(str)<=cur: break
				
				if str[cur]==ignore_pair[ignore_key]:
					break
				cur+=1
			
			ret_list.append(str[start:cur+1])
			cur+=1			
			start=cur


		
		elif (isSplitChar(str[cur])):
			if cur!=start:
				ret_list.append(str[start:cur])	
			ret_list.append(str[cur:cur+1])	
			cur+=1
			start=cur
			
		# スペースで分割
		elif (isSpaceChar(str[cur])):
			if start!=cur:
				ret_list.append(str[start:cur])	
			space=0
			while(1):
				if len(str)<=cur+space: 
					ret_list.append(str[cur:cur+space])	
					start=cur+space
					cur+=space
					break
				if (isSpaceChar(str[cur+space])):
					space+=1
				else:			
					ret_list.append(str[cur:cur+space])	
					start=cur+space
					cur+=space
					break

		else:
			cur+=1

	if start!=cur:
		ret_list.append(str[start:cur])	
	return ret_list
		
def ary2str(ary):
	ret=""
	for elm in ary:
		ret+=elm
	return ret

def ary2str_offset(ary,offset=0):
	ret=""
	for i in range(offset,len(ary)):
		ret+=ary[i]
	return ret

# シンタックスの開始インデックス
def get_lex_index(ary, lex,start):
	i=0
	for elm in ary:
		if elm.lower()==lex.lower():
			return i
		i+=1
	return None

# ステートメントのインデックス取得
def get_keyword_index(ary, offset=0):
	for i in range(offset,len(ary)):
		if len(ary[i])==0: continue
		if isSpaceChar(ary[i][0])==False:
			return i
		i+=1
	return None

# ステートメントのインデックス取得
def get_line_end(ary):
	last_enable_idx=-1
	i=0
	for i in range(0,len(ary)):
		if len(ary)==0: continue
		if ary[i]=="'":			
			return last_enable_idx
		
		if isSpaceChar(ary[i])==False:
			last_enable_idx=i
	
	return  last_enable_idx
	

# 型名を変換
def type_convert(type_name):
	ptrFlag=False
	#　CaseのためにここでPtrを外す
	if type_name.find("Ptr") > -1:
		type_name=type_name.replace("Ptr","")
		ptrFlag=True

	if type_name.lower()=="long":
		ret="int32_t"
	elif type_name.lower()=="dword":
		ret="uint32_t"
	elif type_name.lower()=="integer":
		ret="int16_t"
	elif type_name.lower()=="word":
		ret="uint16_t"
	elif type_name.lower()=="char":
		ret="char"
	elif type_name.lower()=="byte":
		ret="uint8_t"
	elif type_name.lower()=="double":
		ret="double"
	elif type_name.lower()=="single":
		ret="float32_t"
	elif type_name.lower()=="bool":
		ret="bool"
	elif type_name.lower()=="void":
		ret="void"
	elif type_name.lower()=="string":
		ret="char*"
	else:
		ret=type_name
		if ret.find("*") > -1:
			ret=ret.replace("*","")
			ret+="*"

	if ptrFlag:
		ret+="*"

	return ret

def process_declaration(ary):
	for i in range(2,len(ary)):
		if ary[i].lower()=="as":
			tmp=ary[i-2]	#変数名
			ary[i-2] = type_convert(ary[i+2]) # 型名を移動
			ary[i+2]=tmp # 変数名を移動
			
			ary[i+1]="" # 空白
			ary[i+0]="" # AS
	return ary

# dim文を変換
def dim_convert3(elm,keyword_idx,separator_char):

	if len(elm) >= (keyword_idx+4):
		tmp=elm[keyword_idx+0]	#変数名
		elm[keyword_idx+0] = type_convert(elm[keyword_idx+4]) # 型名を移動
		elm[keyword_idx+4]=tmp # 変数名を移動
		
		#区切り文字
		elm[keyword_idx+4]+=separator_char

		elm[keyword_idx+1]="" # 空白
		elm[keyword_idx+2]="" # AS
		keyword_idx+=5
		while(True):
			break
			if len(elm) <= (keyword_idx):	break

			if elm[keyword_idx].count(","):
				next_idx=get_keyword_index(elm,keyword_idx+1)
				if next_idx!=None: 
					elm[keyword_idx]=" "
				#	return dim_convert(elm,next_idx,separator_char)

			keyword_idx+=1

		return ary2str(elm)
	else:
		return "Syntax Error [DIM] !!!!!!!!!!!!!!!"

enum_name=""
enum_line=""
type_name=""
last_type_line_start=9999
in_class=False
in_routine=False
class_name=""

LINE_TYPE_ON_HEADER = 1
LINE_TYPE_ON_CPP=2
LINE_TYPE_BOSH=3

CPP_MODE=0
HEADER_MODE=1
ONEFILE_MODE=2

Mode=CPP_MODE
def ab_syntax_convert(abline):
	global enum_name
	global enum_line
	global type_name
	global last_type_line_start
	global class_name
	global in_class
	global in_routine

	line_type=-1

	# この言語 Gotoがないので、そのための無限ループ
	while(True):
		elm=ab_split(abline)

		trans_line="<unset>"		
		
		keyword_idx=get_keyword_index(elm)
		if keyword_idx==None:
			if Mode!=HEADER_MODE:
				return "// "+abline
			else:
				return None

		keyword=elm[keyword_idx].lower()
		if keyword=="end" or keyword=="else" or keyword=="select":
			#スペースを削ってendif,endsub,endfunction, elseif, selectcaseなどにする
			if len(elm)-1>keyword_idx:
				elm[keyword_idx+1]=""
				elm=ab_split(ary2str(elm))
				keyword=elm[keyword_idx].lower()

		if keyword=="if" or keyword=="elseif":
			if keyword=="if": elm[keyword_idx]="if("
			elif keyword=="elseif": elm[keyword_idx]="} else if("
			then_idx=get_lex_index(elm,"then",keyword_idx)

			#一行if文なら終了させる
			if then_idx!=None and len(elm)-1>then_idx:
				elm[then_idx]="){"
				oneline_statement=ary2str_offset(elm,then_idx+1)
				line_end=get_line_end(elm)
				for i in range(then_idx+1,line_end+1):
					elm[i]=""
				elm[then_idx+1]=ab_syntax_convert(oneline_statement)
				if elm[then_idx+1]==None:
					elm[then_idx+1]=""
				elm[line_end]+=" }"

			trans_line=ary2str(elm).replace("=","==")
			trans_line=re.sub(r" [Aa][Nn][Dd] ", " && ", trans_line)
			trans_line=re.sub(r" [Oo][Rr] ", " || ", trans_line)
			line_type=LINE_TYPE_ON_CPP
		
		elif keyword=="else":
			trans_line="} else {"
			line_type=LINE_TYPE_ON_CPP
			
		elif keyword=="endif" or keyword=="endsub" or keyword=="endfunction":
			elm[keyword_idx]="}"
			trans_line=ary2str(elm)
			if keyword=="endif":
				line_type=LINE_TYPE_ON_CPP
			else:
				if Mode==HEADER_MODE:
					line_type=LINE_TYPE_ON_CPP
				else:
					line_type=LINE_TYPE_BOSH
				in_routine=False

		elif keyword=="exitsub":
			elm[keyword_idx]="return;"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_CPP
		
		elif keyword=="const":
			elm[keyword_idx]="#define"
			trans_line=ary2str(elm).replace("="," ")
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="with":
			elm[keyword_idx]="// ----- with "
			trans_line=ary2str(elm)+" -----"
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="endwith":
			elm[keyword_idx]="// --- end with ---"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="sub":
			# コンストラクタの時はvoidをつけない
			if in_class and (elm[keyword_idx+2]==class_name or elm[keyword_idx+2]=="~"+class_name):
				elm[keyword_idx]=""
				elm[keyword_idx+1]=""
			else:
				elm[keyword_idx]="void"

			# ヘッダモードの時はプロトタイプ宣言にする
			if Mode==HEADER_MODE:
				elm[get_line_end(elm)]+=";"
			else:
				elm[get_line_end(elm)]+=" {"
				
			elm=process_declaration(elm)

			# クラス内でCPPモードの時はクラス名：：をつける
			if in_class and Mode==CPP_MODE :
				elm[keyword_idx+1]+=class_name+"::"

			trans_line=ary2str(elm).replace(",)",")").replace(")(","")

			line_type=LINE_TYPE_BOSH
			in_routine=True

		elif keyword=="function":
			return_type_idx=get_line_end(elm)
			elm[keyword_idx]=type_convert(elm[return_type_idx])
			elm[return_type_idx]="" 	#型名削除
			elm[return_type_idx-1]=""   #ASのスペース
			elm[return_type_idx-2]=""   #AS削除
			elm[return_type_idx-3]=""   #スペース

			if in_class and Mode==CPP_MODE:
				elm[keyword_idx+1]+=class_name+"::"
	
			if Mode==HEADER_MODE:
				elm[get_line_end(elm)]+=";"
			else:
				elm[get_line_end(elm)]+=" {"

			elm=process_declaration(elm)
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_BOSH
			in_routine=True

		elif keyword=="class":
			elm[keyword_idx]="class"
			class_name=elm[keyword_idx+2]
			elm[get_line_end(elm)]+=" {"
			trans_line=ary2str(elm)
			in_class=True
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="endclass":
			elm[keyword_idx]="};"
			trans_line=ary2str(elm)
			in_class=False
			class_name=""
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="public":
			elm[keyword_idx]="public:"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="private":
			elm[keyword_idx]="private:"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_HEADER
			
		elif keyword=="protected":
			elm[keyword_idx]="protected:"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="selectcase":
			elm[keyword_idx]="switch("
			elm[keyword_idx+2]+=") {"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="endselect":
			elm[keyword_idx]="}"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="case":
			elm[keyword_idx]="case"
			elm[keyword_idx+2]+=":"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="goto":
			elm[keyword_idx]="goto"
			trans_line=ary2str(elm).replace("*","")+";"
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="declare":
			elm[keyword_idx]="// Declare"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="typedef":
			elm[keyword_idx]="typedef"
			trans_line=ary2str(elm).replace("=","")
			line_type=LINE_TYPE_ON_HEADER

			# イコールを抜いて再解析
			elm=ab_split(trans_line)
			keyword_idx=get_keyword_index(elm)

			tmp=elm[keyword_idx+2]
			elm[keyword_idx+2]=type_convert(elm[keyword_idx+4])
			elm[keyword_idx+4]=tmp

			trans_line=ary2str(elm)+";"
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="print":
			if len(elm) > (keyword_idx+1):
				elm[keyword_idx+0]="printf"
				elm[keyword_idx+1]="("
				elm[get_line_end(elm)]+=");"
				trans_line=ary2str(elm)
			else:
				trans_line="printf(\"\\n\");"
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="dim":
			elm[keyword_idx+0]=""
			elm[keyword_idx+1]=""
			elm=process_declaration(elm)
			elm[get_line_end(elm)]+=";"
			#elm[keyword_idx+2]+=";"
			trans_line=ary2str(elm).replace(",",";")#dim_convert(elm,keyword_idx+2,";")
			line_type=LINE_TYPE_ON_CPP

		elif keyword=="#console":
			elm[keyword_idx+0]="#include <stdio.h>"
			trans_line=ary2str(elm)
			line_type=LINE_TYPE_BOSH

		#goto label
		elif len(elm[keyword_idx])>0 and elm[keyword_idx][0]=="*":
			elm[get_line_end(elm)]+=":"
			trans_line=ary2str(elm).replace("*","")
			line_type=LINE_TYPE_ON_CPP

		# ------- type文の処理 ---------
		elif keyword=="type":
			type_name=elm[keyword_idx+2]
			trans_line="typedef struct {"
			line_type=LINE_TYPE_ON_HEADER

		elif keyword=="endtype":
			if type_name=="":
				print("Syntax Error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

			trans_line="} "+type_name+";" 
			type_name=""
			line_type=LINE_TYPE_ON_HEADER

		elif type_name!="":
			# 変数宣言
			if len(elm) >= (keyword_idx+4):
				
				last_type_line_start = len(trans_line)
				elm=process_declaration(elm)
				elm[get_line_end(elm)]+=";"
				trans_line=ary2str(elm)#dim_convert(elm,keyword_idx,";")

			else:
				trans_line=ary2str(elm)

			line_type=LINE_TYPE_ON_HEADER
		# ---------- END ------------
		

		# ------- enum文の処理 ---------
		# Endが来るまで出力しない		
		elif keyword=="enum":
			enum_name=elm[keyword_idx+2]
			enum_line="enum "+enum_name+" {\n"
			line_type=LINE_TYPE_ON_HEADER
			return None

		elif keyword=="endenum":
			if enum_name=="":
				print("Syntax Error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

			# 前の行のカンマを削除
			comma_idx=enum_line.index(",",last_type_line_start)
			trans_line=enum_line[:comma_idx]+" "+enum_line[comma_idx+1:]

			trans_line+="} ;" 
			enum_name=""
			line_type=LINE_TYPE_ON_HEADER

		elif enum_name!="":
			last_idx=get_line_end(elm)
			if last_idx!=None:
				elm[last_idx]+=","

			last_type_line_start = len(enum_line)
			enum_line+=ary2str(elm)+"\n"#dim_convert(elm,keyword_idx)
			line_type=LINE_TYPE_ON_HEADER
			return None
		# ---------- END ------------
		
		else:
			# クラス内の変数宣言		
			if in_class and (not in_routine) and (len(elm)>(keyword_idx+2)) and elm[keyword_idx+2].lower()=="as":
				elm=process_declaration(elm)#dim_convert(elm,keyword_idx,";")
				elm[get_line_end(elm)]+=";"
				trans_line=ary2str(elm)
				line_type=LINE_TYPE_ON_HEADER
				
			elif elm[keyword_idx][0]=="#":
				trans_line=ary2str(elm)
				line_type=LINE_TYPE_BOSH

			else:					
				# なんかステートメントがある or 1こある状態だったらセミコロンつける
				if (len(elm)-1)>keyword_idx or (keyword_idx==get_line_end(elm)):
					line_end=get_line_end(elm)
					elm[line_end]+=";"
					trans_line=ary2str(elm)
					line_type=LINE_TYPE_ON_CPP
				else:
					trans_line=ary2str(elm)
					line_type=LINE_TYPE_ON_CPP
		break

	then_idx=get_lex_index(elm,"then",keyword_idx)
	if then_idx!=None:
		elm[then_idx]=") {"


	if (Mode==CPP_MODE and line_type==LINE_TYPE_ON_CPP) or (Mode==HEADER_MODE and line_type==LINE_TYPE_ON_HEADER) or line_type==LINE_TYPE_BOSH or Mode==ONEFILE_MODE:
		return trans_line
	else:
		return None



#main
# if not __debug__:
args = sys.argv
if len(args) != 3:
	print("usage:\n\tpython ab2c.py filename")
	exit(1)

if args[2].lower()=="h":
	Mode=HEADER_MODE
	print("#ifndef "+str(args[1].upper()).replace(".","_"))
	print("#define "+str(args[1].upper()).replace(".","_"))
elif args[2].lower()=="cpp":
	Mode=CPP_MODE
else:
	Mode=ONEFILE_MODE

f = open(args[1])
# else:
# 	Mode=CPP_MODE
# 	f = open("D:\\My-File\Data\\Programs\\ActiveBasic\\_RGBALib\\ab2c\\FT232HLib_debug.sbp")

s1 = f.read()
f.close()

s1=s1.replace("&H","0x")
s1=s1.replace(";","\n")
s1=s1.replace(":",";")
#s1=s1.replace("<>","!=")
#s1=s1.replace("><","!=")
s1=s1.replace("calloc","malloc")
s1=s1.replace("TRUE","true")
s1=s1.replace("FALSE","false")
s1=s1.replace("ByVal","")
s1=s1.replace("ByRef","/* ByRef */")
s1=s1.replace("FALSE","false")
s1=s1.replace("ex\"","\"")
lines = s1.split("\n")

enum_name=""
print(message)
print("#include <stdint.h>")
print("#include <stdbool.h>")
print("#include <windows.h>")
print("#define AB_TO_C")

for il in range(len(lines)):
	if len(lines[il])==0 and Mode!=HEADER_MODE:
		print("")
		continue

	csyntax = ab_syntax_convert(lines[il])
	if csyntax==None: continue
	

	#処理後文字変換
	csyntax=csyntax.replace("'","//")
	csyntax=re.sub(r" [Aa][Nn][Dd] ", " & ", csyntax) # if文の中のAndOrは ifの中で変換しているので大丈夫
	csyntax=re.sub(r" [Oo][Rr] ", " | ", csyntax)
	csyntax=re.sub(r" [Nn][Oo][Tt]", " !", csyntax)
	csyntax=csyntax.replace("<>","!=").replace("><","!=")

	#print(str.format("{}: {}",il,csyntax))
	print(csyntax)
	
if Mode==HEADER_MODE:
	print("#endif")