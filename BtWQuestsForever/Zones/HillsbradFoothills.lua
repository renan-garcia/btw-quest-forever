local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.HillsbradFoothills
local Chain = BtWQuests.Constant.Chain.Forever.HillsbradFoothills
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCity538 = 160701

AddChain(Chain.ClassStormwindCity538, CATEGORY_ID, L["StormwindCity_HillsbradFoothills_538"], { 538, 542 }, 38, 38, 20, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1424),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851080,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCity538,
        },
    },
})

