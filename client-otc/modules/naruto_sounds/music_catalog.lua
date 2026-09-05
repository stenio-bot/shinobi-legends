-- GERADO por tools/audio/gen_music.py a partir da sintese procedural (nao edite a mao).
-- Fonte da verdade: assets-src/audio/music_catalog.json (mesmo conteudo).
-- regiao -> {file='naruto/music/x.ogg', gain=0..1, region={x1,x2,y1,y2}, priority=N}
NarutoMusicCatalog = {
	rate = 22050,
	loop_fade_s = 3.0,
	resolve_order = {'vila', 'floresta_morte', 'costa', 'ruinas', 'montanha', 'covil', 'floresta_vila'},
	tracks = {
		['vila'] = {file = 'naruto/music/vila.ogg', gain = 0.35, priority = 10, title = 'Vila da Folha', region = {x1 = 1010, x2 = 1049, y1 = 1030, y2 = 1069}},
		['floresta_vila'] = {file = 'naruto/music/floresta_vila.ogg', gain = 0.32, priority = 1, title = 'Floresta da Vila', region = {x1 = 1000, x2 = 1129, y1 = 1000, y2 = 1119}},
		['costa'] = {file = 'naruto/music/costa.ogg', gain = 0.38, priority = 8, title = 'Costa das Mares', region = {x1 = 1000, x2 = 1049, y1 = 1120, y2 = 1169}},
		['floresta_morte'] = {file = 'naruto/music/floresta_morte.ogg', gain = 0.4, priority = 8, title = 'Floresta da Morte', region = {x1 = 1130, x2 = 1199, y1 = 1000, y2 = 1119}},
		['ruinas'] = {file = 'naruto/music/ruinas.ogg', gain = 0.38, priority = 8, title = 'Ruinas do Cla Marionetista', region = {x1 = 1200, x2 = 1249, y1 = 1000, y2 = 1049}},
		['montanha'] = {file = 'naruto/music/montanha.ogg', gain = 0.4, priority = 8, title = 'Montanha do Trovao', region = {x1 = 1200, x2 = 1249, y1 = 1060, y2 = 1109}},
		['covil'] = {file = 'naruto/music/covil.ogg', gain = 0.42, priority = 8, title = 'Covil da Nuvem Vermelha', region = {x1 = 1400, x2 = 1449, y1 = 1000, y2 = 1049}},
	},
}
