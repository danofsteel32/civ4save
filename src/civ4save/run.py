from civ4save import save_file, structure

save = save_file.read("tests/saves/bismark-emperor-turn86.CivBeyondSwordSave")
fmt = structure.get_format(debug=True)
fmt.parse(save, max_players=19)
