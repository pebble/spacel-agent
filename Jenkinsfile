dockerBuild {
    name = 'pwagner/spacel-agent'
    testCommand = 'docker-compose up test'
    reports = [
        tests: '**/build/nosetests.xml',
        tasks: '**/*.py'
    ]
}

