dockerBuild {
    name = 'pwagner/spacel-agent'
    testCommand = 'make composetest'
    reports = [
        tests: '**/build/nosetests.xml',
        tasks: '**/*.py'
    ]
}

