#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""catalog.json builder.

製品マスター: source sheet 1u7gmxyvmV8j5AbgBKDk37v5LJXYNpAA6UsoF2nVMaZU（下記 ROWS に固定）。
ダイブ詳細  : dive_master.json（Google Sheet「月刊みんなのダイブ_デザインリスト」
              ID 13yXVppzgcE0NyY0ATZ7JdiCaYtNzBJ4wMVH_1HBEopk の全項目スナップショット）を
              各 S-MZ 製品の "dive" に丸ごと保持する。
ビルド時もシートを読まずローカルの dive_master.json で完結（提案生成も catalog.json のみ参照）。
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))

# (type, model, name, category, exTax, incTax, jan, can, legacyName, fileId, note)
ROWS = [
("ボード","S-BD-AA1","スクーミーオレンジボード","中心",3000,3300,"4573676920584","測った値を読み取り数字や色・音・画面・バーで出力する中心の部品","オレンジボード","1TyNzfFeDwEvfOgqfuYygVKYBdFvQpYlz",""),
("アクセサリ","S-UT-AA1","書き込み機（オレンジボード専用）","中心",3000,3300,"","つくったプログラムをボードに書き込む","書き込み機","15AKzoCQ2c1xZ3YYggNDDcilBekV0tzaH",""),
("アクセサリ","S-CB-A02","コネクター延長ケーブル","補助",700,770,"","センサーや表示を離して置ける","延長ケーブル","1y_E9U6hHfE2018FtnX8b9nOrxSIgPlGz","高解像度JPG"),
("標準16","S-CN-A01","タッチセンサーコネクター","入力",1000,1100,"","指で触れたことを感知できます","タッチセンサー","18wRLyaZtLO4FSLO8KKJN0Z8CiDR0wrap",""),
("標準16","S-CN-A02","スイッチコネクター","入力",1000,1100,"","押したことを感知できます","スイッチ","1SGAb_IlxSTKDIPaL5RJOfoKN0tqUt7Fv",""),
("標準16","S-CN-A03","明るさセンサーコネクター","入力",1000,1100,"","明るさが測れます","明るさセンサー","1uZ17R-NlGaIq7bG8zPDBOgNtSVzeT598",""),
("標準16","S-CN-A04","磁気センサーコネクター","入力",1000,1100,"","磁力を測れます","磁気センサー","1-VNl1n22rhm35S17SBxDYnBVpCTbLRq4",""),
("標準16","S-CN-A05","通過センサーコネクター","入力",1500,1650,"","通過を感知できます","通過センサー","1Ok5TQ41FGoqQBtnm0rssMCIF7P-N_0ga",""),
("標準16","S-CN-A06","音センサーコネクター","入力",1500,1650,"","音量を測れます","音センサー","1w7aXNUz5vrdWRnX5GKbyLg5sQlI1F6yh",""),
("標準16","S-CN-A07","赤外線受信コネクター","入力",1500,1650,"","赤外線を受信できます","赤外線受信コネクター","16kHpNFG5SJDEriW1hNk5X23tWu9MFD4H",""),
("標準16","S-CN-A08","土壌水分センサーコネクター","入力",2000,2200,"","土壌の水分量が測れます","土壌水分センサー","1gPUpgljl_HBBI-V7YKA-U0TwW04LPL7R",""),
("標準16","S-CN-A09","温度センサーコネクター","入力",2000,2200,"","温度が測れます","温度センサーコネクター","1rfmF53UWVT34NB9fV14Rz-OwzOc1Ogfp",""),
("標準16","S-CN-A10","加速度センサーコネクター","入力",2000,2200,"","加速度が測れます","加速度センサーコネクター","1xm6PQlK8y3BHX2-qLuhL83gMcFrhzqY6",""),
("標準16","S-CN-A11","距離センサーコネクター","入力",2000,2200,"","距離が測れます","距離センサーコネクター","1kPndGViBM9vQJcy3cuEM8VmKP6XRT_Sh",""),
("標準16","S-CN-A12","LEDコネクター","出力",1000,1100,"","LEDライトの発光ができます（単灯単色）","LED","1yuMTgx1ICR9PHWVgd2pyKpjGP0TahL5S",""),
("標準16","S-CN-A13","7SEGコネクター","表示",1500,1650,"","数値の表示ができます","7SEG","1CankGf3Ewsodq-DmB2IP2j2IV248h7Fb",""),
("標準16","S-CN-A14","フルカラーLEDコネクター","出力",1500,1650,"","LEDライトの発光ができます（単灯複数色）","フルカラーLED","1suI5n2BeD6iEkXutn0KjPm2HNBWCT5fb",""),
("標準16","S-CN-A15","赤外線送信コネクター","出力",1500,1650,"","赤外線を送信できます","赤外線送信","1Hs4wJ55Wkomk29TL7gyQWvak_6Bex6Y7",""),
("標準16","S-CN-A16","スピーカーコネクター","出力",2000,2200,"","ドレミでつくったメロディを鳴らせます","スピーカー","1u98o04mML2iInN9DG7vt0W1NZO_JR3aB",""),
("追加24","S-CN-B01","振動スイッチコネクター","入力",1500,1650,"","揺れを感知できます","振動スイッチ","1n9kNJMpkDp02ejKw972sb0lKMrImhRXE",""),
("追加24","S-CN-B02","USBコネクター","入力",1500,1650,"","USB-Aを接続できます","USB","1PcYWSKXmXC7f7RWUyHmuLtgcjHLt3-gu",""),
("追加24","S-CN-B03","雨センサーコネクター","入力",2000,2200,"","雨を感知できます","雨センサー","1tZqzRTI92XQAZnLHIT9k3o41FCAcaQoi",""),
("追加24","S-CN-B04","湿度センサーコネクター","入力",2000,2200,"","湿度が測れます","湿度センサー","1hizWSubr4zYhk6FPqskwfY9QU9woZvdO",""),
("追加24","S-CN-B05","気圧センサーコネクター","入力",2000,2200,"","気圧が測れます","気圧センサー","11XqzGgZaNXgqThANUjoj_Nvi5RTFAU63",""),
("追加24","S-CN-B06","水温センサーコネクター","入力",2000,2200,"","水温を測れます","水温センサー","11HnvMIBFNP_3uKANXvqqbeUXDkwgwiD9",""),
("追加24","S-CN-B07","人感センサーコネクター","入力",2000,2200,"","人を感知できます","人感センサー","1MtxOjtMDMoq7lmTSY4u6wECnfjvExIBW",""),
("追加24","S-CN-B08","圧力センサーコネクター","入力",5000,5500,"","圧力を測れます","圧力センサー","1-vrLtBGhKDOXNALbf-NbL8wYlLcsrtAp",""),
("追加24","S-CN-B09","アルコールセンサーコネクター","入力",3000,3300,"","気化アルコールの濃度が測れます","アルコール","1_EaTBGx2KpNKIuMqUAWKgElNcGUtpR_e",""),
("追加24","S-CN-B10","曲げセンサーコネクター","入力",4000,4400,"","曲げを感知できます","曲げセンサー","1VLjZGPwQ4ha71XzXjsppMbes-EIzk2Of",""),
("追加24","S-CN-B11","GPSセンサーコネクター","入力",7000,7700,"","緯度・経度が測れます","GPS","1UoDSEJ1Slto90x7Se9GFAg5Z3zl1PZdo",""),
("追加24","S-CN-B12","水流センサーコネクター","入力",7000,7700,"","水流が測れます","水流センサー","1g16SZgJEbtvEc4yhzk-nnnqY38ErgA6V",""),
("追加24","S-CN-B13","アンモニアセンサーコネクター","入力",10000,11000,"","気化アンモニアの濃度が測れます","アンモニア","1zP8itPp-VQbUzxf1wvH0LjS01XTYyEpi",""),
("追加24","S-CN-B14","トグルスイッチコネクター","入力",1500,1650,"","ONまたはOFFと別のONへの切り替えができます","トグルスイッチ","1NF3zCPIhU9ilwC6UGjXMoUsGobs3IXlV",""),
("追加24","S-CN-B15","スライドスイッチコネクター","入力",1000,1100,"","ONまたはOFFができます","スライドスイッチ","1oyqA5RB6PvDDW0-ehZG5GGWQrmbex4zf",""),
("追加24","S-CN-B16","フェーダーコネクター","入力",2000,2200,"","無段階で値を変化させられます","フェーダー","1MP8IyLo_U4Zr_pZl9xPCeyn7fTr3X3BI",""),
("追加24","S-CN-B17","振動モーターコネクター","出力",1500,1650,"","振動させられます","振動モータ","1E9CwAcyDnBK7I-vjsY57n5ILlCnjAhtT",""),
("追加24","S-CN-B18","プロペラモーターコネクター","出力",2000,2200,"","プロペラ付きモーターを動かせます","プロペラ","19Lt3hs8dxL0wuwVv8ajEfduSWqXHPbsI",""),
("追加24","S-CN-B19","OLEDコネクター","表示",2000,2200,"","文字の表示ができます","OLED","1hm1cXY-IThUdNkgPzd_1fPUZD6oXPFUv",""),
("追加24","S-CN-B20","180度回転サーボモーターコネクター","出力",2500,2750,"","角度指定ができるモーターを動かせます","180","11jXPmJ50501ES7M2MB9TpG2ZBmbzxyER",""),
("追加24","S-CN-B21","ポンプコネクター","出力",3000,3300,"","ポンプで水を汲み上げます（別途チューブ必要）","ポンプ","1wloE8Ka1cQy9zSknJA1zJZLsIQ4le52h",""),
("追加24","S-CN-B22","LEDバーコネクター","出力",2000,2200,"","LEDライトの発光ができます（複数灯複数色）","LEDバー","1Vxuj7KDKQ9B9cSq83gihnSt_ZESNo144",""),
("追加24","S-CN-B23","TTモーターコネクター","出力",2500,2750,"","ギア付きモーターを動かせます","TTモーター","1mSCuV9ZSAaG__oWjTWWR7A4UNujOOhns",""),
("追加24","S-CN-B24","SDカードコネクター","記録",3000,3300,"","データを別売りのmicroSDに保存できます（オレンジボード専用）","SDカードコネクター","1HgVlzHPfqIgkl_oU2UriI6nlyiwh-pNI",""),
("教材","S-MZ-A02","みんなのダイブ 土壌水分を測りに行こう初回増量","教材",1500,1650,"4573676920041","ピックアップ:土壌水分センサー。芝自由研究で採用","","1ojArMMs_mK7s__tEMhPWLSnDEzMIyMRg",""),
("教材","S-MZ-A03","みんなのダイブ 土壌水分を測りに行こう中巻","教材",1500,1650,"4573676920171","ピックアップ:土壌水分センサー","","1nmCjdQm9Te4DW1KGDClwH2-RflSkGJK0",""),
("教材","S-MZ-A04","みんなのダイブ 土壌水分を測りに行こう下巻","教材",1500,1650,"4573676920188","ピックアップ:土壌水分センサー","","1Vf5814d0tv56Qx4OXSJZpc_qHFET5eKM",""),
("教材","S-MZ-A05","みんなのダイブ 冷蔵庫にくっつく強さを測りに行こう","教材",1500,1650,"4573676920195","ピックアップ:磁力センサー（本田技研監修）","","1N1Z_8H4qxoCYaDsLPEDNw10lDHkMf4rx",""),
("教材","S-MZ-A06","みんなのダイブ特集号 はじめての課題解決2025","教材",1500,1650,"4573676920270","ピックアップ:タッチセンサー","","14wdklBygcsLUmuQEK5Lk6j4nsp5Ai0J8",""),
("教材","S-MZ-A09","みんなのダイブ特集号 はじめてのセンサーと測定","教材",1500,1650,"4573676920300","ピックアップ:タッチセンサー","","1PkMOuoY8r_q3hQuVlPGmH4C0LseZ5841",""),
("教材","S-MZ-A11","みんなのダイブ特集号 はじめてのWeb API","教材",1500,1650,"4573676920317","ピックアップ:温度センサー","","104PrR_QxEjSvfz94MJgEW6Mx6bfh-Oou",""),
("教材","S-MZ-A12","みんなのダイブ 自転車のこぎやすさを測りに行こう","教材",1500,1650,"4573676921123","ピックアップ:磁力センサー（本田技研監修）","","1Ph0g9MIxpm9RG5uj6CBgA9Rke-FEY7S-",""),
("教材","S-MZ-A13","みんなのダイブ 通学路の課題を解決しに行こう","教材",1500,1650,"4573676921130","ピックアップ:磁力センサー（本田技研監修）","","1B03USWub_8OUpLTWolWurbqiGnPQT7W-",""),
("教材","S-MZ-A14","みんなのダイブ特集号 アサガオの土の水分を測りに行こう","教材",1500,1650,"4573676921178","ピックアップ:土壌水分センサー（上中下合体特集号）","","1sy7wxKZf52mMtvseUWa4aYAvyh8rz8La",""),
("教材","S-MZ-A15","みんなのダイブ すいかばマンを探しに行こう","教材",1500,1650,"4573676921185","ピックアップ:角度・加速度センサー（ロッテ監修）","","1euER5NlwTMUVuIv0Ig0krjBrqy6XLck2",""),
("教材","S-MZ-A16","みんなのダイブ Unityでゲームをつくろう","教材",1500,1650,"4573676921246","ピックアップ:角度・加速度センサー（ロッテ監修・Unity号）","","1jF6Bu02YLkfOAT8eodRWaVatcNiDQKg1",""),
("教材","S-MZ-A17","みんなのダイブ特集号 Sense the World Touch Measure Create","教材",1500,1650,"4573676921208","ピックアップ:タッチセンサー（英語版）","","1GEwK9wGPY_qkIAEw001RUY5m3bbpFCpq",""),
("教材","S-MZ-A18","みんなのダイブ特集号 はじめての情報I","教材",1500,1650,"4573676921253","ピックアップ:タッチセンサー","","1QtXxlD-W1OBotb3wU0ab0-S2QpyCq4El",""),
("教材","S-MZ-A19","みんなのダイブ特集号 ウェブでデータを比べよう","教材",1500,1650,"4573676921260","ピックアップ:明るさセンサー","","1gGwOhedHoz9oKzBorspwjuBFb1r93Emf",""),
]

def load_dive_master():
    """dive_master.json（ダイブ全項目スナップショット）を model→dict で返す。無ければ空。"""
    p=os.path.join(ROOT,"dive_master.json")
    if not os.path.exists(p):
        print("⚠ dive_master.json が見つかりません。ダイブ詳細なしで生成します。")
        return {}, {}
    d=json.load(open(p,encoding="utf-8"))
    return d.get("byModel",{}), d

def main():
    dive_by_model, dive_doc = load_dive_master()
    products = []
    for t,model,name,cat,ex,inc,jan,can,legacy,fid,note in ROWS:
        rec = {
            "model": model, "type": t, "name": name, "category": cat,
            "priceExTax": ex, "priceIncTax": inc, "jan": jan or None,
            "can": can, "legacyName": legacy or None,
            "photoFileId": fid or None,
            "image": f"img/{model}.png" if fid else None,
            "note": note or None,
        }
        if model in dive_by_model:
            # ダイブ号は全項目を dive にそのまま保持（表示側で必要分だけ抜き出す）
            rec["dive"] = dive_by_model[model]
        products.append(rec)
    doc = {
        "meta": {
            "title": "SchooMy 提案アセットカタログ（マスター）",
            "version": "v1.3", "updated": "2026-06-08",
            "sourceSheet": "1u7gmxyvmV8j5AbgBKDk37v5LJXYNpAA6UsoF2nVMaZU",
            "diveSheet": "13yXVppzgcE0NyY0ATZ7JdiCaYtNzBJ4wMVH_1HBEopk",
            "diveFields": dive_doc.get("fields"),
            "diveFieldsJa": dive_doc.get("fieldsJa"),
            "joinKey": "model",
        },
        "products": products,
    }
    with open(os.path.join(ROOT,"catalog.json"),"w",encoding="utf-8") as f:
        json.dump(doc,f,ensure_ascii=False,indent=2)
    miss=[p["model"] for p in products if not p["photoFileId"]]
    nd=sum(1 for p in products if p.get("dive"))
    print("products:",len(products),"| with photo:",sum(1 for p in products if p['photoFileId']),
          "| with dive:",nd,"| no photo:",miss)

if __name__=="__main__":
    main()
