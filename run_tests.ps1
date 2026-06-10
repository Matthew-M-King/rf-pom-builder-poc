param(
    [switch]$Headless
)

$headlessValue = if ($Headless) { "True" } else { "False" }

robot --variable headless:$headlessValue --variable target_app:SwagLabs --include swaglabs --outputdir Tests/Reports/SwagLabs .
robot --variable headless:$headlessValue --variable target_app:ChallengingDom --include ChallengingDom --outputdir Tests/Reports/ChallengingDom .
