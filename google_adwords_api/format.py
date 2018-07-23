def get_report_fields(client):
    print('\nGetting report fields for...')
    report_fields = {}

    for report_type in REPORT_TYPES:
        print('%s' % report_type)
        report_definition_service = client.GetService('ReportDefinitionService',
                                                      version=ADWORDS_VERSION)
        fields = report_definition_service.getReportFields(report_type)
        report_fields[report_type] = fields
    return report_fields

def filter_report_fields(report, fields):
    # TODO: not necessarily the fields we want, but this set prevents errors
    incompatible_fields = set()
    
    if 'Date' in fields:
        incompatible_fields = incompatible_fields.union({
            'Week', 'DayOfWeek', 'Month', 'MonthOfYear', 'Quarter', 'Year'})

    if 'ActiveViewCpm' in fields:
        incompatible_fields = incompatible_fields.union({
            'ConversionCategoryName', 'ConversionTrackerId',
            'ConversionLagBucket', 'ConversionTypeName', 'ExternalConversionSource'})
    if 'AllConversionRate' in fields:
        incompatible_fields = incompatible_fields.union({'HourOfDay', 'Slot'})
    if 'AverageCpe' in fields:
        incompatible_fields = incompatible_fields.union({
            'ClickType', 'ConversionCategoryName', 'ConversionTrackerId',
            'ConversionTypeName', 'ExternalConversionSource'})
    if 'AverageCost' in fields:
        incompatible_fields = incompatible_fields.union({
            'ConversionCategoryName' , 'ConversionTrackerId',
            'ConversionTypeName', 'ExternalConversionSource'})
    if 'AverageCpm' in fields:
        incompatible_fields = incompatible_fields.union({
            'ConversionCategoryName', 'ConversionTypeName',
            'ConversionTrackerId', 'ExternalConversionSource'})
    if 'AverageCpv' in fields:
        incompatible_fields = incompatible_fields.union({
            'ClickType', 'ConversionCategoryName', 'ConversionTypeName',
            'ExternalConversionSource'})
    if 'AverageFrequency' in fields:
        incompatible_fields = incompatible_fields.union({
            'ClickType', 'ConversionCategoryName', 'ConversionTrackerId',
            'ConversionTypeName', 'DayOfWeek', 'Device',
            'ExternalConversionSource', 'HourOfDay', 'Quarter', 'Slot', 'Year'})
    
    incompatible_fields = incompatible_fields.union({
        'AccountTimeZone', 'AccountCurrencyCode', 'AccountDescriptiveName', 
        'CustomerDescriptiveName'})

    for field in incompatible_fields:
        if field in fields:
          fields.remove(field)
    return fields