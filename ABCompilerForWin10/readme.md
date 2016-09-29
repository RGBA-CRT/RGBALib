#ActiveBasic Version 4.24.00 例外無視＆Win10対応パッチ

#なにこれ
Win10の最新ビルドで、ActiveBasic ver4（以下AB4）のBasicCompilerでGUIアプリをデバッグしようとすると
	例外処理 code：e06d7363
と表示されデバッグができない問題（Win10のバグ）があり、MSがなかなか修正しないのでAB4側いじってやろうというものです。
ちなみにWin7以降からの問題である、GetOpenFileNameで0x6BA,0xC0020043が発生して動かない問題も解決されます。

WinIPSなどを用いてオリジナルのBasicCompilerに対して
	BasicCompiler[NoMessage].ips
	BasicCompiler[DBG_EXCEPTION_NOT_HANDLED].ips
の2つのパッチを当ててください。


#改造点：
	・例外処理のMessageBoxをNOPでつぶした
	・ContinueDebugEventの継続モードをDBG_CONTINUEからDBG_EXCEPTION_NOT_HANDLEDにした
	　-> GetOpenFileName/GetSaveFileNameのバグが解決

##パッチの作者
RGBA_CRT 2016 [rgba3crt1p@gmail.com]
	