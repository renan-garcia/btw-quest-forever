local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.Zone16593
local Chain = BtWQuests.Constant.Chain.Forever.Zone16593
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCity93835 = 160301

AddChain(Chain.ClassStormwindCity93835, CATEGORY_ID, L["StormwindCity_Zone16593_93835"], { 93835, 94369, 93089, 94946, 94947, 93963 }, 12, 13, 7, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = L["ZONE_16593"],
    expansion = EXPANSION_ID,
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCity93835,
        },
    },
})

