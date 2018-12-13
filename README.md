# RGBALib
（自分用）ActiveBasic ver4用API定義＆ライブラリ集  
他サイトからのコピペも含まれています。

## 使用方法
ActiveBasicのIncludeディレクトリに配置してください。  
+ RGBADef.sbp
  + Windows APIの関数定義、定数定義が記述されている。RGBALib.sbpをインクルードすると自動で読み込まれる。
+ RGBALib.sbp
  + ライブラリ本体。プログラムからはこれをインクルードする。
+ abcdecl.sbp
  + ActiveBasicからcdecl関数を呼べるようにするライブラリ。
+ EasyIO.sbp
  + ファイル操作を簡単にする関数集。これは使わないでRGBALibのFileクラスを使ってください。
+ EasyHID.sbp
  + USB HIDデバイスを簡単に使えるようにするライブラリ。

## ActiveBasicCompiler for Win10
Win10にてGUIアプリがデバッグできない（例外コード:0xe06d7363）のを修正するパッチを作りました。
GetOpenFileName/GetSaveFileNameのバグも治ります。
詳しくはABCompilerForWin10/readme.mdを参照。

## highlight.js for ActiveBasic
ABをハイライトする。詳しくはhighlightディレクトリへ。

## ab2c
AB -> C を手助け

## testprogram
ABで書いたテストプログラム集。ゴミ溜め。コピペあり。黒歴史あり。読みやすく書いていない。

## cdeclLoaderのソース
clang用
```
int __stdcall cdeclLoader(funcPtr func,int *params,unsigned char nParam){
	int addesp=4*nParam;

	//引数をスタックに積む
	if(params!=NULL){
		for(int i=nParam;i!=0;i--){
			int pval=params[i-1];
			__asm{
				push pval
			}
		}
	}

	//call function
	int ret;
	__asm{
		nop
		call func		//関数呼び出し
		add esp,addesp	//引数を積んだスタックを戻す
		mov	 ret,eax	//戻り値を保存
	}

	return ret;	
}
```
