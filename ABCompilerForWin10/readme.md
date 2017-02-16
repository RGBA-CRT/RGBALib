#ActiveBasic Version 4.24.00 例外無視＆Win10対応パッチ

#なにこれ
Win10の最新ビルドで、ActiveBasic ver4（以下AB4）のBasicCompilerでGUIアプリをデバッグしようとすると
	例外処理 code：e06d7363  
と表示されデバッグができない問題（Win10のバグ）があり、MSがなかなか修正しないのでAB4側いじってやろうというものです。  
ちなみにWin7以降からの問題である、GetOpenFileNameで0x6BA,0xC0020043が発生して動かない問題も解決されます。

WinIPSなどを用いてオリジナルのBasicCompilerに対して[BasicCompilerForWin10.ips]を当ててください。
それを[BasicCompiler.exe]にリネームして使ってください。

#チェックサム
	オリジナルのCRC32: 748B18A9
	パッチ後のCRC32　: D549402B
	サイズ: 319488バイト (0 MB)

#改造点：
	・例外処理のMessageBoxをNOPでつぶした
	・不明な例外発生時にContinueDebugEventの継続モードをDBG_CONTINUEからDBG_EXCEPTION_NOT_HANDLEDにした
	　-> GetOpenFileName/GetSaveFileNameのバグが解決

##パッチの作者
RGBA_CRT 2016 [rgba3crt1p@gmail.com]
	