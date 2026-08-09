# Munkafolyamat

Státusz: Elfogadva
Tulajdonos: Horváth Gyula Attila
Létrehozva: 2026-08-09
Utolsó módosítás: 2026-08-09
Kapcsolódó dokumentumok: [USER_GUIDE.md](USER_GUIDE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DOMAIN_MODEL.md](DOMAIN_MODEL.md)

## Cél

A `USER_GUIDE.md` azt írja le, *hogyan* kattints végig a felületen. Ez a dokumentum azt írja le, *milyen sorrendben és miért* érdemes a Slice Designer funkcióit használni — a pipeline tényleges adatfolyamára, a paraméterek egymástól való függésére, a bemenet-kimenet összefüggésekre és a gyártási (CNC/lézer/plazma) szempontokra fókuszálva.

## 1. A pipeline adatfolyama

A Futtatás mindig ugyanabban a, felhasználó által nem módosítható sorrendben zajlik:

```
Mesh Import → Slice Engine → [Dowel Engine] → [Gap Engine] → [Backplate Engine] → Numbering Engine → Nesting Engine
```

majd külön, önálló lépésként: **DXF Export** (a Futtatástól leválasztva — tetszőlegesen sokszor exportálhatsz ugyanabból az eredményből, új Futtatás nélkül).

Amit fontos tudni erről a sorrendről:

* A **Dowel**, a **Gap** (Spacer) és a **Backplate** lépés szögletes zárójelben szerepel, mert **opcionális** — csak akkor fut le, ha a hozzá tartozó jelölőnégyzet be van kapcsolva. Legalább egyet be kell kapcsolni.
* A **Numbering** és a **Nesting** mindig lefut, függetlenül attól, hogy a fenti három közül melyik aktív.
* A Dowel **mindig előbb** fut, mint a Gap — a Dowel a modell geometriája alapján, önállóan foglalja el a helyét, a Spacer-ek ehhez igazodnak (ahol lehet, a Spacer a Dowel pozíciójára kerül, csak a hiányzó darabszámig kap önálló helyet). Ez fordítva nem működne: ha a Spacer foglalná el a helyet előbb, a Dowel nem tudna a modell geometriája szerint optimálisan átfűződni.
* **Fontos, könnyen elfelejthető részlet:** a Gap Engine kimenete (a Spacer-lista) **megkerüli** a Backplate Engine-t és a Numbering Engine-t — egyenesen a Nesting Engine bemenete. A Spacer-ek tehát sosem kapnak Backplate-kapcsolódást és sosem kapnak Numbering-azonosítót (nincs is rá szükségük — egyszerű korongok).
* A Numbering csak a Backplate után futhat, mert a Backplate-hez kapcsolódó szigetekhez a Backplate megfelelő pozícióján is el kell helyeznie az azonosítót.

## 2. Paraméterezési sorrend

Bár a paraméter-panel minden mezője egyszerre látható, van egy logikus kitöltési sorrend, mert néhány paraméter **korlátozza** a többi lehetséges értékét:

1. **`slice_axis` először.** Ez határozza meg, hogy a másik két tengely közül melyik választható `backplate_normal_axis`-nak és `numbering_normal_axis`-nak — mindkettő kötelezően a `slice_axis`-tól *eltérő* tengely, előjellel.
2. **`numbering_direction_axis_sign` a `numbering_normal_axis` után.** Ennek a `slice_axis`-tól és a `numbering_normal_axis`-tól is különböznie kell (a harmadik, megmaradó tengely előjele) — enélkül a Futtatás konfigurációs hibával leáll.
3. **Ha Dowel *és* Gap is aktív:** a két panel Spacer-átmérő mezőjét (`dowel_diameter_mm` mellett a Dowel panel saját `spacer_diameter_mm`-je, illetve a Gap panel `spacer_diameter_mm`-je) egyeztetni kell — a program ellenőrzi, eltérés esetén hibát jelez.
4. **A Nesting anyagtáblázatát csak azután érdemes kitölteni, hogy a szeletvastagság (és ha van, a Backplate-vastagság) véglegesült** — a `slice_material_id` vastagságának pontosan egyeznie kell a szeletvastagsággal, a `backplate_material_id`-nak a Backplate-vastagsággal. Ez a leggyakoribb forrása a "Futtatás a Nesting-nél hibával leáll" jelenségnek, ha valaki utólag módosítja a szeletvastagságot, de elfelejti frissíteni az anyagtáblázatot.
5. **A `numbering_normal_axis` és a `backplate_normal_axis` egymástól függetlenek** — nem kell, hogy megegyezzenek, és nincs is köztük automatikus kapcsolat (ez szándékos: az azonosítót akkor is el tudod helyezni egy adott oldalon, ha nincs Backplate).

## 3. Bemenet → kimenet elvárások

**Milyen STL-lel dolgozik jól a rendszer:**

* Vízzáró (manifold), egybefüggő geometria — a nem-vízzáró modell is betöltődik, csak figyelmeztetéssel; a további lépések (elsősorban a szeletelés zárt kontúr elvárása) viszont megkövetelik, hogy a metszősík mindig zárt keresztmetszetet adjon.
* Plauzibilis méret (alapértelmezetten 1–3000 mm bármely tengelyen) — ha a modell ennél kisebb/nagyobb, valószínűleg rossz mértékegységben (pl. méterben vagy hüvelykben) lett exportálva; érdemes az eredeti CAD-szoftverben ellenőrizni és újraexportálni, mielőtt a szeletelési paramétereket finomhangolnád.

**Mikor várható hiba a szeletelésnél:** a szeletvastagság és a Gap kombinációjának a modell méretéhez képest legfeljebb 2%-os eltéréssel kell illeszkednie (a rendszer eddig a mértékig automatikusan, egyenletesen átskálázza a modellt). Ha ennél nagyobb a szükséges korrekció, válassz olyan szeletvastagságot/Gap-et, ami jobban osztja a modell szeletelési tengely menti méretét.

**Hogyan hat a modell geometriája a Dowel/Backplate eredményre:**

* Sok kis, egymástól elkülönülő sziget szeletenként → minden szigetet igyekszik lefedni legalább egy Dowel, ami a `dowel_count_per_region` célszámnál több Dowel-t is eredményezhet — ez szándékos, nem hiba.
* Elágazó (pl. Y- vagy T-alakú) régiók → a Dowel automatikus keresése lassabb (pontos, erózió-alapú pont-tartalmazás tesztet igényel), de a végeredmény ugyanúgy determinisztikus.
* Erősen egyenetlen, sok apró érintkezési felületű geometria a Backplate oldalán → nagyobb eséllyel fordul elő, hogy egyes szigetek a domináns közös síktól eltérnek, és figyelmeztetéssel kimaradnak a Backplate-kapcsolódásból — ez nem hiba, de érdemes az állapotnaplóban ellenőrizni, hány sziget maradt ki.
* Nagyon vékony/apró metszet-régiók → könnyebben ütköznek a `min_dowels_per_region`/`min_spacers_per_region` minimumba; ha ez hibát okoz, csökkentsd a minimumot, vagy vastagítsd a szeletet.

## 4. CNC gyártási szempontból fontos korlátozások

A Slice Designer **technológia-független**: a munkafolyamat a DXF Export előállításával lezárul, a tényleges gépvezérlés (G-code generálás, a gép saját szoftvere) nem a program feladata — bármilyen lézervágó, CNC maró vagy plazmavágó munkafolyamatba illeszthető, amely DXF-et fogad be.

Amit ennek fényében figyelembe kell venni:

* **A `kerf_mm` csak az elrendezésnél (Nesting) számít** — a darabok közötti minimális távolságként. A tényleges vágási rés a te géped/szerszámod tulajdonsága; ha ez eltér a Nesting-nél megadott értéktől, a darabok a lapon túl szorosan vagy túl lazán fognak elférni.
* **A CUT és az ENGRAVE réteg elnevezését/színét a saját vágó-szoftvered fogja értelmezni** — a Slice Designer csak két, névvel és színnel megkülönböztetett réteget ír a DXF-be; hogy ebből a te szoftvered milyen tényleges vágási/gravírozási teljesítményt csinál, az a te beállításod, nem a Slice Designeré.
* **Az anyagvastagság-egyezés (Nesting anyagtáblázat vs. tényleges szeletvastagság/Backplate-vastagság) csak a tervezési modellen belüli konzisztenciát ellenőrzi** — nem helyettesíti a tényleges alapanyag lemért vastagságát. Ha a beszerzett alapanyag vastagsága eltér a tervezettől, az illesztések (Dowel-furat, csap/fészek) szorossága ennek megfelelően változik.
* **A toldási varrat pusztán vágásvonal** — nincs hozzá automatikusan generált illesztő-geometria (pl. saját furat vagy csap); a toldott daraboknak a vágás után, kézzel kell összeilleszkedniük (pl. ragasztással, hátlappal, külön rögzítőelemmel). Ezt a program tervezéskor jelzi (al-azonosítóval megjelölve minden toldott darabot), de fizikailag nem old meg.
