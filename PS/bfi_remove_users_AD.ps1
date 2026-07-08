import-module activedirectory
$ListInput = "D:\BigFix_Account_Maintenance\PS\BFI_All_Cores_Inactive_DN.txt"
$SourceGroup = @("Group1", "Group2")
$SourceDomain = 'InsertDomain'

Function Get-DomainFromDNString($strADsPath) {
    if ($strADsPath.startsWith('DC=')) {
        ($strADsPath.Replace("DC=", ".").Replace(',', '')).Substring(1)
    }
    Else {
        $strADsPath.Substring($strADsPath.IndexOf(",DC")).Replace(",DC=", ".").Substring(1)
    }
}

#Import user list
$RemoveList = (Get-content -path $ListInput)

#Iterate thru SourceGroups to get the actual AD Object
$Groups = $SourceGroup | Foreach {
    Get-ADGroup $_ -server $SourceDomain #bind to Group
}

#Build out your user list of AD Objects
$Users = $removeList | Foreach {
    $MemDomain = (Get-DomainFromDNString $_)
    Get-ADUser $_ -server $MemDomain #bind to user
}
#Iterate thru your groups and remove in bulk all users
$Groups | Foreach {
    Write-Host $Users
    Remove-ADGroupMember -Identity $_ -Members $Users -Confirm:$false
}