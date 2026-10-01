local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.WesternPlaguelands
local Chain = BtWQuests.Constant.Chain.Forever.WesternPlaguelands
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCity6182 = 160901

AddChain(Chain.ClassStormwindCity6182, CATEGORY_ID, L["StormwindCity_WesternPlaguelands_6182"], { 6182, 6183, 6186 }, 60, 60, 56, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1422),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851112,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCity6182,
        },
    },
})

