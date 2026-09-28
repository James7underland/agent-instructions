Выполни проверку на основании роли в [`review_rules_detailed.md`](review_rules_detailed.md) с учетом правил:
- [`naming.md`](naming.md)
- [`comments.md`](comments.md)
- [`calcs.md`](calcs.md)
- [`tests.md`](tests.md)
- [`dry.md`](dry.md)
- [`namespace.md`](namespace.md)
- [`rule_of_7.md`](rule_of_7.md)

Проверяй только файлы, в которых выполнялись изменения данного MR:
```bash
git diff --name-only origin/main...HEAD
```

Сохрани результат в .md-файл, начинающийся со слова `report`.
