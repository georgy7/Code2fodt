#Code2fodt

Скрипт для компактного архивирования исходников
в&nbsp;человекочитаемой форме
с&nbsp;помощью обыкновенного принтера.

Вдохновлено [Arctic Code Vault](https://archiveprogram.github.com/arctic-vault/).

Требования:

* Git-репозиторий.
  * Программа печатает только tracked файлы.
  * У&nbsp;бинарных файлов печатается только размер в&nbsp;байтах и&nbsp;MD5.
* Кодировка UTF-8 у всех текстовых файлов.
* ПО:
  * Git
  * File (реализация, поддерживающая `--mime-encoding`)
  * OpenOffice / LibreOffice
  * Можно использовать AbiWord для распечатки больших документов (поддерживает ODT).
    ```
    libreoffice --headless --convert-to odt out.fodt
    ```
* Надежный носитель. Например:
  * [Бескислотная бумага ♾](https://en.wikipedia.org/wiki/Acid-free_paper) из&nbsp;древесного сырья&nbsp;—
  после полного намокания,
  *если она не&nbsp;порвётся в&nbsp;намокшем виде,*
  после высыхания она останется лишь немного деформированной.
  Возможно, книга из&nbsp;такой бумаги сможет даже пережить потоп и&nbsp;не&nbsp;слипнуться.
  Тестировал слипание двух листов.
  Полностью пропитывал их водой и&nbsp;оставлял соединенными до&nbsp;полного высыхания
  в&nbsp;горизонтальном положении при комнатной температуре, ничем не&nbsp;прижимая.
  Листы не&nbsp;слиплись, но после неоднократного намокания и&nbsp;высыхания
  бумага становится немного ворсистой на&nbsp;микроуровне, чернила немного стираются. 
  Бескислотная бумага не&nbsp;только хорошо переносит воду, но также
  медленнее разрушается от&nbsp;света и&nbsp;тепла.
  Стандарты:
    * [ISO 9706](https://www.iso.org/standard/17562.html)
    * [ГОСТ Р ИСО 9706-2000](https://internet-law.ru/gosts/gost/10997/).
    В&nbsp;2007 году на&nbsp;Снегурочке указывалось соответствие этому стандарту.
    Собственно, старую пачку Снегурочки я и&nbsp;тестеровал.
    Сейчас интернет-магазины обычно не&nbsp;указывают этот стандарт в&nbsp;фильтрах.
    Я&nbsp;даже не&nbsp;смог нагуглить, соответствует&nbsp;ли Снегурочка сейчас этому стандарту или нет. 
      * Не&nbsp;путать с&nbsp;ГОСТ&nbsp;Р&nbsp;57641-2017&nbsp;— про размеры, смачиваемость, требования к упаковке.
      * Не&nbsp;путать с&nbsp;ГОСТ&nbsp;Р&nbsp;ИСО 9001-2015&nbsp;— стандарт клиентоориентированности организации.
  * Архивная/музейная бумага для очень важных документов.
  Например, 100% хлопковая бумага, устойчивая не&nbsp;только к&nbsp;воде, но и к&nbsp;механическому истиранию.
  Не&nbsp;знаю, совместима&nbsp;ли она вообще с&nbsp;лазерными принтерами.
  Видел в&nbsp;продаже только в&nbsp;зарубежных интернет-магазинах.
  Стандарты:
    * [ISO 11108](https://www.iso.org/standard/1708.html)
  * Ламинирование&nbsp;— еще один способ защиты от&nbsp;воды и&nbsp;механических повреждений.
  Минусы: долго, сложно, утяжеляет размер архива в 2-3 раза.
  * Была идея потестировать прозрачные плёнки (термопленки, не&nbsp;самоклеющиеся).
  Есть пленки A4 для лазерной печати.
  Продаются обычно по 10-50 листов в пачке.
  Значительно дороже бумаги. Довольно большой разброс цен.
  Полиэстр (ПЭТ) лёгкий, тонкий, нерастворим в воде,
  температура плавления&nbsp;— 250&nbsp;°C.
  Может быть токсичен при горении. Менее удобно читать и&nbsp;сканировать.
  * Фотобумага&nbsp;— есть водостойкие виды.
  Фотобумага специально предназначена для длительного хранения.
  Чуть дешевле плёнок. Не прозрачная, белый фон.
  Минусы: скорее всего подходит только для струйной печати;
  намного тяжелее плёнок.
* Принтер (для трехколоночного шаблона желательно 2400 dpi).
* 10-кратная или более мощная лупа или сканер, чтобы читать распечатки.
* Скрепление листов.
  * Например, дырокол и папка-регистратор или
  * Настоящий живой переплётчик (переплёт выглядит солидно,
  но если придется в будущем сканировать&nbsp;— это неудобно).
