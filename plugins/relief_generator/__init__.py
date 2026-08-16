"""Relief Generator plugin — opcionális `MeshSource` a SliceDesignerhez.

Parametrikus relief-modelleket (pl. hullámfelület alapú domborzatokat) állít
elő, és a `MeshSource` contracton (ADR-0014) keresztül kapcsolódik a
SliceDesigner core-hoz. A plugin a core-tól fizikailag elkülönített,
`src/slicedesigner/` alól semmit nem importáló csomag (ADR-0015, ADR-0016).

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md.
"""
