--[[
    WoW Forever reports interface 16001, which is below 90000, so the retail
    addon takes the pre-Shadowlands API path. Forever uses the Midnight API.
]]

local interfaceVersion = select(4, GetBuildInfo()) or 0

BTWQUESTS_IS_FOREVER = interfaceVersion >= 16000 and interfaceVersion < 20000

function BtWQuests_UseLegacyQuestLog()
    if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo then
        return false
    end
    return true
end

function BtWQuests_HasModernChrome()
    if BTWQUESTS_IS_FOREVER then
        return true
    end
    return interfaceVersion >= 100000
end

function BtWQuests_HasWarband()
    return C_QuestLog
        and C_QuestLog.IsQuestFlaggedCompletedOnAccount
        and GetAccountPlayerLevel
end
