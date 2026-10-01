local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.Darkshore
local Chain = BtWQuests.Constant.Chain.Forever.Darkshore
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCityOtherAlliance = 161101

AddChain(Chain.ClassStormwindCityOtherAlliance, CATEGORY_ID, L["StormwindCity_Darkshore_OtherAlliance"], { 97914 }, 17, 17, 13, true, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1439),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851074,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCityOtherAlliance,
        },
    },
})

