function slNewSubsystem(path, pos)
%SLNEWSUBSYSTEM  Пустая подсистема (без стандартных In1 -> Out1).
%   slNewSubsystem('mdl/ПИ-регулятор', [260 265 380 335])
%   Внутрь затем добавлять 'simulink/Sources/In1' и 'simulink/Sinks/Out1'
%   с осмысленными именами (e, u) - они станут подписями портов снаружи.
add_block('simulink/Ports & Subsystems/Subsystem', path, 'Position', pos);
delete_line(path, 'In1/1', 'Out1/1');
delete_block([path '/In1']);
delete_block([path '/Out1']);
end
