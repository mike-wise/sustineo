

<#
.SYNOPSIS
    Grants data plane role-based access control for Azure Cosmos DB NoSQL accounts.

.DESCRIPTION
    This script implements the complete process to grant data plane access to Azure Cosmos DB NoSQL accounts
    based on Microsoft documentation. It handles role definition retrieval and role assignment creation.

.PARAMETER ResourceGroupName
    The name of the resource group containing the Cosmos DB account.

.PARAMETER AccountName
    The name of the Azure Cosmos DB NoSQL account.

.PARAMETER PrincipalId
    The object ID of the identity (user, service principal, or managed identity) to grant access to.
    If not provided, uses the current signed-in user.

.PARAMETER RoleDefinitionId
    The ID of the role definition to assign. If not provided, uses the built-in "Cosmos DB Built-in Data Contributor" role.

.PARAMETER Scope
    The scope for the role assignment. If not provided, uses the entire Cosmos DB account scope.

.PARAMETER ListRoleDefinitions
    Switch to list all available role definitions for the account.

.PARAMETER ListRoleAssignments
    Switch to list all current role assignments for the account.

.EXAMPLE
    .\Grant-CosmosDBDataPlaneAccess.ps1 -ResourceGroupName "myResourceGroup" -AccountName "myCosmosAccount"
    
    Grants the built-in Data Contributor role to the current signed-in user for the specified Cosmos DB account.

.EXAMPLE
    .\Grant-CosmosDBDataPlaneAccess.ps1 -ResourceGroupName "myResourceGroup" -AccountName "myCosmosAccount" -PrincipalId "12345678-1234-1234-1234-123456789012"
    
    Grants the built-in Data Contributor role to the specified principal ID for the Cosmos DB account.

.EXAMPLE
    .\Grant-CosmosDBDataPlaneAccess.ps1 -ResourceGroupName "myResourceGroup" -AccountName "myCosmosAccount" -ListRoleDefinitions
    
    Lists all available role definitions for the specified Cosmos DB account.

.NOTES
    Author: Generated based on Microsoft Azure Cosmos DB documentation
    Requires: Azure CLI or Azure PowerShell module
    Prerequisites:
    - Azure account with active subscription
    - Existing Azure Cosmos DB NoSQL account
    - Appropriate control plane permissions:
      * Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions/read
      * Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments/read
      * Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments/write
#>

[CmdletBinding(DefaultParameterSetName = 'GrantAccess')]
param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $true)]
    [string]$AccountName,
    
    [Parameter(ParameterSetName = 'GrantAccess')]
    [string]$PrincipalId,
    
    [Parameter(ParameterSetName = 'GrantAccess')]
    [string]$RoleDefinitionId,
    
    [Parameter(ParameterSetName = 'GrantAccess')]
    [string]$Scope,
    
    [Parameter(ParameterSetName = 'ListRoles')]
    [switch]$ListRoleDefinitions,
    
    [Parameter(ParameterSetName = 'ListAssignments')]
    [switch]$ListRoleAssignments
)

# Function to check if Azure CLI is available and user is logged in
function Test-AzureCLI {
    try {
        $null = az account show 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Not logged in to Azure CLI. Please run 'az login' first."
            return $false
        }
        return $true
    }
    catch {
        Write-Error "Azure CLI is not installed or not available in PATH. Please install Azure CLI."
        return $false
    }
}

# Function to get the built-in Data Contributor role definition ID
function Get-BuiltInDataContributorRoleId {
    param(
        [string]$ResourceGroup,
        [string]$Account
    )
    
    Write-Host "Retrieving built-in role definitions..." -ForegroundColor Yellow
    
    $roleDefinitions = az cosmosdb sql role definition list `
        --resource-group $ResourceGroup `
        --account-name $Account `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve role definitions. Check your permissions and account details."
    }
    
    $builtInRole = $roleDefinitions | Where-Object { $_.roleName -eq "Cosmos DB Built-in Data Contributor" }
    
    if (-not $builtInRole) {
        throw "Built-in Data Contributor role not found. This role should be available by default."
    }
    
    Write-Host "Found built-in Data Contributor role: $($builtInRole.id)" -ForegroundColor Green
    return $builtInRole.id
}

# Function to get current user's principal ID
function Get-CurrentUserPrincipalId {
    Write-Host "Getting current signed-in user information..." -ForegroundColor Yellow
    
    $userInfo = az ad signed-in-user show --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to get current user information. Make sure you're logged in to Azure CLI."
    }
    
    Write-Host "Current user: $($userInfo.displayName) ($($userInfo.id))" -ForegroundColor Green
    return $userInfo.id
}

# Function to get Cosmos DB account scope
function Get-AccountScope {
    param(
        [string]$ResourceGroup,
        [string]$Account
    )
    
    Write-Host "Getting Cosmos DB account information..." -ForegroundColor Yellow
    
    $accountInfo = az cosmosdb show `
        --resource-group $ResourceGroup `
        --name $Account `
        --query "{id:id}" `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve account information. Check your permissions and account details."
    }
    
    Write-Host "Account scope: $($accountInfo.id)" -ForegroundColor Green
    return $accountInfo.id
}

# Function to create role assignment
function New-RoleAssignment {
    param(
        [string]$ResourceGroup,
        [string]$Account,
        [string]$RoleDefId,
        [string]$Principal,
        [string]$AssignmentScope
    )
    
    Write-Host "Creating role assignment..." -ForegroundColor Yellow
    Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Cyan
    Write-Host "  Account: $Account" -ForegroundColor Cyan
    Write-Host "  Role Definition ID: $RoleDefId" -ForegroundColor Cyan
    Write-Host "  Principal ID: $Principal" -ForegroundColor Cyan
    Write-Host "  Scope: $AssignmentScope" -ForegroundColor Cyan
    
    $assignment = az cosmosdb sql role assignment create `
        --resource-group $ResourceGroup `
        --account-name $Account `
        --role-definition-id $RoleDefId `
        --principal-id $Principal `
        --scope $AssignmentScope `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create role assignment. Check your permissions and parameters."
    }
    
    Write-Host "Role assignment created successfully!" -ForegroundColor Green
    return $assignment
}

# Function to list role definitions
function Show-RoleDefinitions {
    param(
        [string]$ResourceGroup,
        [string]$Account
    )
    
    Write-Host "Listing all role definitions for account '$Account'..." -ForegroundColor Yellow
    
    $roleDefinitions = az cosmosdb sql role definition list `
        --resource-group $ResourceGroup `
        --account-name $Account `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve role definitions."
    }
    
    Write-Host "`nRole Definitions:" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    
    foreach ($role in $roleDefinitions) {
        Write-Host "`nRole Name: $($role.roleName)" -ForegroundColor Cyan
        Write-Host "Role Type: $($role.typePropertiesType)" -ForegroundColor White
        Write-Host "Role ID: $($role.id)" -ForegroundColor White
        Write-Host "Data Actions:" -ForegroundColor White
        foreach ($action in $role.permissions[0].dataActions) {
            Write-Host "  - $action" -ForegroundColor Gray
        }
    }
}

# Function to list role assignments
function Show-RoleAssignments {
    param(
        [string]$ResourceGroup,
        [string]$Account
    )
    
    Write-Host "Listing all role assignments for account '$Account'..." -ForegroundColor Yellow
    
    $assignments = az cosmosdb sql role assignment list `
        --resource-group $ResourceGroup `
        --account-name $Account `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve role assignments."
    }
    
    Write-Host "`nRole Assignments:" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Green
    
    if ($assignments.Count -eq 0) {
        Write-Host "No role assignments found." -ForegroundColor Yellow
        return
    }
    
    foreach ($assignment in $assignments) {
        Write-Host "`nAssignment ID: $($assignment.id)" -ForegroundColor Cyan
        Write-Host "Principal ID: $($assignment.principalId)" -ForegroundColor White
        Write-Host "Role Definition ID: $($assignment.roleDefinitionId)" -ForegroundColor White
        Write-Host "Scope: $($assignment.scope)" -ForegroundColor White
    }
}

# Main script execution
try {
    Write-Host "Azure Cosmos DB Data Plane Access Control Script" -ForegroundColor Magenta
    Write-Host "=================================================" -ForegroundColor Magenta
    
    # Check Azure CLI availability
    if (-not (Test-AzureCLI)) {
        exit 1
    }
    
    # Handle different parameter sets
    switch ($PSCmdlet.ParameterSetName) {
        'ListRoles' {
            Show-RoleDefinitions -ResourceGroup $ResourceGroupName -Account $AccountName
            return
        }
        'ListAssignments' {
            Show-RoleAssignments -ResourceGroup $ResourceGroupName -Account $AccountName
            return
        }
        'GrantAccess' {
            # Get role definition ID if not provided
            if (-not $RoleDefinitionId) {
                $RoleDefinitionId = Get-BuiltInDataContributorRoleId -ResourceGroup $ResourceGroupName -Account $AccountName
            }
            
            # Get principal ID if not provided
            if (-not $PrincipalId) {
                $PrincipalId = Get-CurrentUserPrincipalId
            }
            
            # Get account scope if not provided
            if (-not $Scope) {
                $Scope = Get-AccountScope -ResourceGroup $ResourceGroupName -Account $AccountName
            }
            
            # Create the role assignment
            $assignment = New-RoleAssignment -ResourceGroup $ResourceGroupName -Account $AccountName -RoleDefId $RoleDefinitionId -Principal $PrincipalId -AssignmentScope $Scope
            
            Write-Host "`nRole assignment details:" -ForegroundColor Green
            Write-Host "Assignment ID: $($assignment.id)" -ForegroundColor White
            Write-Host "Principal ID: $($assignment.principalId)" -ForegroundColor White
            Write-Host "Role Definition ID: $($assignment.roleDefinitionId)" -ForegroundColor White
            Write-Host "Scope: $($assignment.scope)" -ForegroundColor White
            
            # Verify the assignment by listing all assignments
            Write-Host "`nVerifying role assignment..." -ForegroundColor Yellow
            Show-RoleAssignments -ResourceGroup $ResourceGroupName -Account $AccountName
            
            Write-Host "`nData plane access has been successfully granted!" -ForegroundColor Green
            Write-Host "You can now use this identity to access data in your Cosmos DB account." -ForegroundColor Green
        }
    }
}
catch {
    Write-Error "An error occurred: $($_.Exception.Message)"
    exit 1
}

Write-Host "`nScript completed successfully!" -ForegroundColor Green
