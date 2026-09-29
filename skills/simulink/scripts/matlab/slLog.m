function slLog(sys, blk, k)
%SLLOG  Включить журналирование выхода k блока (сигнал попадает в
%   out.logsout и в Simulation Data Inspector под именем линии).
%   Имя задаётся на линии: set_param(L, 'Name', 'x'). Модели нужно
%   set_param(mdl, 'SignalLogging', 'on', 'SignalLoggingName', 'logsout').
if nargin < 3, k = 1; end
ph = get_param([sys '/' blk], 'PortHandles');
set_param(ph.Outport(k), 'DataLogging', 'on');
end
