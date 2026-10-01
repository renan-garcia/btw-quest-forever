local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.ElwynnForest
local Chain = BtWQuests.Constant.Chain.Forever.ElwynnForest
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.Series1 = 160201
Chain.Series2 = 160202
Chain.Series3 = 160203
Chain.Series4 = 160204
Chain.Series5 = 160205
Chain.Series6 = 160206
Chain.Series7 = 160207
Chain.Series8 = 160208
Chain.Series9 = 160209
Chain.Series10 = 160210
Chain.Series11 = 160211
Chain.Other = 160212
Chain.Neutral = 160213
Chain.ClassStormwindCity343 = 160601
Chain.ClassStormwindCity6403 = 160602

AddChain(Chain.Series1, CATEGORY_ID, L["ElwynnForest_1"], { 91741, 91743, 91745, 91752, 91758, 91772, 91775, 91777 }, 2, 7, 1, false, "Alliance", nil, nil)
AddChain(Chain.Series2, CATEGORY_ID, L["ElwynnForest_2"], { 85, 86, 84, 87 }, 6, 8, 5, false, "Alliance", nil, nil)
AddChain(Chain.Series3, CATEGORY_ID, L["ElwynnForest_3"], { 40, 35, 37, 45, 71, 39, 59 }, 10, 10, 7, false, "Alliance", nil, nil)
AddChain(Chain.Series4, CATEGORY_ID, L["ElwynnForest_4"], { 15, 21 }, 3, 5, 1, false, "Alliance", nil, nil)
AddChain(Chain.Series5, CATEGORY_ID, L["ElwynnForest_5"], { 239, 11 }, 10, 10, 6, false, "Alliance", nil, nil)
AddChain(Chain.Series6, CATEGORY_ID, L["ElwynnForest_6"], { 783, 7 }, 1, 2, 1, false, "Alliance", nil, nil)
AddChain(Chain.Series7, CATEGORY_ID, L["ElwynnForest_7"], { 62, 76 }, 7, 10, 4, false, "Alliance", nil, nil)
AddChain(Chain.Series8, CATEGORY_ID, L["ElwynnForest_8"], { 60, 61 }, 7, 7, 3, false, "Alliance", nil, nil)
AddChain(Chain.Series9, CATEGORY_ID, L["ElwynnForest_9"], { 106, 111, 107, 112 }, 6, 7, 5, false, "Alliance", nil, nil)
AddChain(Chain.Series10, CATEGORY_ID, L["ElwynnForest_10"], { 3903, 3904, 3905 }, 4, 4, 2, false, "Alliance", nil, nil)
AddChain(Chain.Series11, CATEGORY_ID, L["ElwynnForest_11"], { 5261, 33 }, 2, 2, 1, false, "Alliance", nil, nil)
AddChain(Chain.Other, CATEGORY_ID, L["ElwynnForest_Other"], { 91736, 16, 5805, 92124, 18, 6, 54, 2158, 47, 114, 91751, 91753, 99127, 99128, 99129, 99130, 99131, 99143, 83, 88, 5545, 46, 52, 109, 123, 147, 91723, 91724, 91725, 91732, 91733, 91738, 91740, 91746, 176 }, 1, 11, 1, true, "Alliance", nil, nil)
AddChain(Chain.Neutral, CATEGORY_ID, L["ElwynnForest_Neutral"], { 7961, 7962, 95771 }, 1, 10, 1, true, nil, nil, nil)
AddChain(Chain.ClassStormwindCity343, CATEGORY_ID, L["StormwindCity_ElwynnForest_343"], { 343, 344, 345, 347, 346 }, 24, 24, 20, false, "Alliance", nil, nil)
AddChain(Chain.ClassStormwindCity6403, CATEGORY_ID, L["StormwindCity_ElwynnForest_6403"], { 6403, 6501 }, 60, 60, 50, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1429),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851068,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.Series1,
        },
        {
            type = "chain",
            id = Chain.Series2,
        },
        {
            type = "chain",
            id = Chain.Series3,
        },
        {
            type = "chain",
            id = Chain.Series4,
        },
        {
            type = "chain",
            id = Chain.Series5,
        },
        {
            type = "chain",
            id = Chain.Series6,
        },
        {
            type = "chain",
            id = Chain.Series7,
        },
        {
            type = "chain",
            id = Chain.Series8,
        },
        {
            type = "chain",
            id = Chain.Series9,
        },
        {
            type = "chain",
            id = Chain.Series10,
        },
        {
            type = "chain",
            id = Chain.Series11,
        },
        {
            type = "chain",
            id = Chain.Other,
        },
        {
            type = "chain",
            id = Chain.Neutral,
        },
        {
            type = "chain",
            id = Chain.ClassStormwindCity343,
        },
        {
            type = "chain",
            id = Chain.ClassStormwindCity6403,
        },
    },
})

