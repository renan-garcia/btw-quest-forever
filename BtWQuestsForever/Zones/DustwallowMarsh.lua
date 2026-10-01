local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.DustwallowMarsh
local Chain = BtWQuests.Constant.Chain.Forever.DustwallowMarsh
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCityOtherAlliance = 161201

AddChain(Chain.ClassStormwindCityOtherAlliance, CATEGORY_ID, L["StormwindCity_DustwallowMarsh_OtherAlliance"], { 1267, 1324 }, 38, 38, 28, true, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1445),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851099,
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

