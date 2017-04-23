# RGBALib
（自分用）ActiveBasic ver4用API定義＆ライブラリ集  
いろんなサイトからのコピペでも含まれています。

## 使用方法
ActiveBasicのIncludeディレクトリに配置してください。

## ActiveBasicCompiler for Win10
Win10にてGUIアプリがデバッグできない（例外コード:0xe06d7363）のを修正するパッチを作りました。
GetOpenFileName/GetSaveFileNameのバグも治ります。
詳しくはABCompilerForWin10/readme.mdを参照。

## cdeclLoaderのソース
最適化はまだしてない。コンパイルはclangで。
'int __stdcall cdeclLoader(funcPtr func,int *params,unsigned char nParam){
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
'