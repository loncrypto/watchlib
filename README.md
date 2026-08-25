# watchlib

Değişen bir sayıyı terminalde izlemek için: biçimlendirme, renkler, eşikler, alarmlar.

Neyi izlediğini bilmez — ona bir sayı döndüren fonksiyon verirsin. Bu yüzden aynı
döngü bir Uniswap fiyatını da, bir Solana havuzunu da, bir API cevabını da izleyebilir.

## Kurulum

```bash
pip install -e /home/l/dex/watchlib
```

## Kullanım

```python
from watchlib import Watcher

Watcher(
    fetch=lambda: pool.quote_buy(0.1),
    input_amount=0.1, input_label="ETH", output_label="BASECAT",
    higher_means_cheaper=True,    # 1 ETH daha çok token alıyorsa fiyat düşmüştür
    alert_threshold_pct=20,
).run()
```

Çıktı:

```
01:58 0.1000 ETH = 8,846 BASECAT (0%)
02:03 0.1000 ETH = 9,102 BASECAT (-2.8%)
  ! BASECAT: %21.4 dustu (10,745) - alarm #1
    sonraki alarm esigi: %30.0
```

## `higher_means_cheaper` neden var

İzlenen sayı bir **fiyat** değil de bir **miktar** olduğunda ("1 ETH kaç token alır")
sayının artması fiyatın *düştüğü* anlamına gelir. Bu ters çevirmeyi çağıran kodun
içinde `1/x` hesaplarıyla yapmak, sessiz hatalara açık bir yerdir — makul görünen ama
ters yöne bakan bir sayı üretir, hata vermez. Bu yüzden adı konmuş bir parametre
olarak burada duruyor ve testleri var.

## İki eşik, iki iş

| | ne yapar |
|---|---|
| `print_threshold_pct` | Son basılan satırdan bu kadar oynamadıysa tekrar basma. Sakin bir piyasanın ekranı aynı satırla doldurmasını engeller. |
| `alert_threshold_pct` | Başlangıç değerinden bu kadar aşağı düşerse alarm ver. Her alarmdan sonra `alert_backoff` ile genişler, böylece uzun bir düşüş her tick'te değil, aralıkları açılarak raporlanır. |

## Modüller

| Dosya | İçerik |
|---|---|
| `format.py` | Saf fonksiyonlar: `format_number`, `format_change`, `format_duration`, `relative_change`. Ağ yok, çıktı yok, test edilebilir. |
| `console.py` | Renkli basma, renk isimleri, aktifliğe göre renk yükseltme. Süreç başına tek `Console`. |
| `watch.py` | `Watcher` — izleme döngüsü, eşikler, alarm geri çekilmesi, Ctrl+C ile duraklat/devam. |
| `sound.py` | İsteğe bağlı sesli uyarı. Oynatıcı yoksa sessizce geçer; `make_speech()` ile konuşan uyarı dosyası üretilebilir (gtts gerekir). |

## Davranış notları

- **Ctrl+C çıkmaz, duraklatır.** Duraklamışken ikinci Ctrl+C çıkar. İzleme genelde
  başından kalkıp geri dönülen bir şey, kazara kaybedilmemeli.
- **Hatalar döngüyü durdurmaz.** Geçici bir RPC hatası loglanır ve devam edilir;
  `max_errors` verilirse ardışık hata sayısı aşılınca durur.
- **İlk değer alınana kadar ısrar eder** — referans noktası olmadan hiçbir yüzde
  anlamlı değil.

## Test

```bash
python tests/test_watchlib.py
```

Ağ gerektirmez, beklemez (`interval=0`, `max_ticks` ile).
