## Чек-лист Dont repeat yourself

> Этот документ используется при проверке студенческих работ. Нарушения помечаются как замечания к качеству кода.


### Обязательные требования
Нельзя писать длинные сильно повторяющиеся куски кода, они должны быть выделены в отдельную функцию, класс, метод и т.д.

Пример ниже - нужен один более общий create_fluid, который будет вызываться из первого

```c++

template <typename Fluid>
inline std::unique_ptr<Fluid> thermo_db_t::create_fluid(
    const std::vector<std::wstring>& component_list
    , const std::vector<double>& molar_fractions) const
{
    std::vector<const component_properties_t*> components_local;
    components_local.reserve(component_list.size());

    for (const auto& component_id : component_list) {
        if (cas_components.count(component_id) == 1) {
            // Трактуем component_id как CAS. Дублей CAS нет, поэтому проверяем только на count == 1
            const component_properties_t& properties = cas_components.at(component_id);
            components_local.emplace_back(&properties);
        }
        else {
            // Не нашли component_id среди CAS-номеров,
            // Трактуем component_id как формулу, по которой пробуем получить CAS
            const std::wstring& cas = get_casno_by_formula(component_id); // здесь будет exception, если формула не найдется
            const component_properties_t& properties = cas_components.at(cas);
            components_local.emplace_back(&properties);
        }
    }

    if (!molar_fractions.empty()) {
        Eigen::VectorXd fractions = Eigen::VectorXd::Map(
            molar_fractions.data(),
            molar_fractions.size()
        );
        return std::make_unique<Fluid>(components_local, fractions);
    }
    else {
        return std::make_unique<Fluid>(components_local);
    }
};
//*****************************************************************************



template <typename Fluid>
inline std::unique_ptr<Fluid> thermo_db_t::create_fluid(
    const std::vector<std::wstring>& component_list
    , const bip_recalc_plan_t& bip_recalc_plan
    , const std::vector<double>& molar_fractions) const
{
    // Заложим на будущее
    // static_assert(
    //     std::is_same_v<Fluid, vlelib::fluid_peng_robinson_t>,
    //     "thermo_db_t::create_fluid: BIP recalculation is supported only for fluid_peng_robinson_t"
    //     );

    std::vector<const component_properties_t*> components_local;
    components_local.reserve(component_list.size());

    for (const auto& component_id : component_list) {
        if (cas_components.count(component_id) == 1) {
            // Трактуем component_id как CAS. Дублей CAS нет, поэтому проверяем только на count == 1
            const component_properties_t& properties = cas_components.at(component_id);
            components_local.emplace_back(&properties);
        }
        else {
            // Не нашли component_id среди CAS-номеров,
            // Трактуем component_id как формулу, по которой пробуем получить CAS
            const std::wstring& cas = get_casno_by_formula(component_id); // здесь будет exception, если формула не найдется
            const component_properties_t& properties = cas_components.at(cas);
            components_local.emplace_back(&properties);
        }
    }

    std::vector<std::wstring> components_casno_list;
    components_casno_list.reserve(component_list.size());
    for (const auto& comp_cas : components_local) {
        components_casno_list.push_back(comp_cas->CASno);
    }

    Eigen::MatrixXd binary_coeffs_local;
    if (bip_recalc_plan.size()) {
        binary_coeffs_local = estimate_bip_matrix(
            components_casno_list, components_local, bips, bip_recalc_plan);
    }

    if (!molar_fractions.empty()) {
        Eigen::VectorXd fractions = Eigen::VectorXd::Map(
            molar_fractions.data(),
            molar_fractions.size()
        );
        return std::make_unique<Fluid>(components_local, binary_coeffs_local, fractions);
    }
    else {
        return std::make_unique<Fluid>(components_local, binary_coeffs_local);
    }

}
//*****************************************************************************


```