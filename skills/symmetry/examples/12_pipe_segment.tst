# Трубопровод (PipeSegment): вода 200 м³/ч по трубе Øвн 200 мм, 5 км, подъём 30 м — перепад давления.
units SI
hold
$RootThermo = VirtualMaterials.APRNGL2
/ -> $RootThermo
$RootThermo + WATER
go
/W = Stream.Stream_Material()
/W.In.T = 20 C
/W.In.P = 2000 kPa
/W.In.VolumeFlow = 200 m3/h
/W.In.Fraction = 1
/P1 = PipeSegment.PipeSegment("PressureDropModel = ; PressureDropModel = PipeModels.VMGPressureDropModel(); NumberSections = 10; Elevation1 = 0.0 m; U = None; Roughness = 0.045 mm; Length = 10 m")
/P1.In -> /W.Out
/P1.Length = 5000 m
/P1.InnerDiameter = 200 mm
/P1.OuterDiameter = 219 mm
/P1.Elevation1 = 30 m
# теплообмен: без него «Missing 1 specifications». U = 0 — адиабатная труба (или U + /P1.ExternalT)
/P1.U = 0 W/m2-K
/W2 = Stream.Stream_Material()
/W2.In -> /P1.Out
/P1.DeltaP
/W2.Out.P
/W2.Out.T
