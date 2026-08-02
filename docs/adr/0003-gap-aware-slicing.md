# ADR-0003: Gap figyelembevétele a Slice Engine szeletelésekor

Dátum: 2026-08-01
Státusz: Elfogadva
Döntéshozó: Horváth Gyula Attila (projektgazda)

## Kontextus

A SLICE_ENGINE_SPEC.md kidolgozása során (Phase 2) derült ki, hogy az ARCHITECTURE.md eredeti Slice Engine / Gap Engine felelősség-felosztása hiányos volt: nem rögzítette, hogy az összeállított modellnek (szeletek + hézagok együtt) az eredeti Mesh méretét kell kiadnia a szeletelési tengely mentén. Emiatt a Slice Engine nem határozhatja meg helyesen a szeletek számát és pozícióját a Gap ismerete nélkül — ez ellentmond annak, hogy a Slice Engine Domain Model kapcsolata eredetileg nem tartalmazta a Gap-et.

A projekt célja (PROJECT_VISION.md és a projektgazda kiegészítése alapján): egy, a Luban stacking-funkciójához hasonló, de hézag- és hátlap-támogatással kiegészített, licencköltség nélküli saját eszköz — ahol a hézagok az eredeti modell méretén belül helyezkednek el, nem azon felül.

## Döntés

A Gap paraméter bekerül a Slice Engine bemenetei és Domain Model kapcsolatai közé. A Slice Engine felelőssége kibővül: a szeleteket úgy pozicionálja, hogy a szeletek összvastagsága és a köztük lévő Gap-ek összege pontosan kiadja a Mesh szeletelési tengely menti méretét. A Gap Engine felelőssége ennek megfelelően szűkül: a pozicionálás helyett kizárólag a Spacer geometria előállításáért felel, a Slice Engine által már helyesen elhelyezett Slice Set alapján.

## Mérlegelt alternatívák

* **Gap Engine végzi a pozicionálást is** (eredeti terv) — egyszerűbb Slice Engine, de ekkor a Slice Engine nem tudja előre, hány szeletet kell készítenie ahhoz, hogy a végeredmény kiadja az eredeti méretet; a két engine közötti hallgatólagos, utólagos újraszámítási függés bonyolultabb és kevésbé átlátható lenne, mint egy explicit bemeneti paraméter.
* **A modell mérete és a Gap független marad** — a Slice Engine a Gap figyelembevétele nélkül szeletel, a végső összeállított méret eltérhet az eredetitől. Elvetve, mert nem felel meg a projektgazda tervezési szándékának.
* **Gap figyelembevétele a Slice Engine-ben** (*választott*) — a szeletek és hézagok együtt pontosan az eredeti Mesh méretét adják ki; a Gap Engine felelőssége letisztul (kizárólag Spacer előállítás).

## Következmények

* Az `ARCHITECTURE.md` Slice Engine és Gap Engine szakasza, valamint a 3. szakasz (Adatfolyam) vonatkozó mondata frissül.
* A `DOMAIN_MODEL.md` "Fogalmi kapcsolatok" szakasza kiegészül egy új tétellel.
* A `SLICE_ENGINE_SPEC.md` (Phase 2, még folyamatban lévő specifikáció) tartalmát ennek megfelelően kell újrafogalmazni.
* Nincs érintett forráskód (Phase 4 még nem kezdődött el).
